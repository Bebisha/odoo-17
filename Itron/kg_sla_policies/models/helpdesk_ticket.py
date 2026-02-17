from datetime import time, timedelta

import pytz

from odoo import models, fields, api
from odoo.osv import expression


class HelpDeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    sla_status_ids = fields.One2many('helpdesk.sla.status', 'ticket_id', string="SLA Status")
    sla_deadline_hours = fields.Float("Hours to SLA Deadline", compute='_compute_sla_deadline', compute_sudo=True,
                                      store=True)

    sla_deadline = fields.Datetime("SLA Deadline", compute='_compute_sla_deadline', compute_sudo=True, store=True)

    sla_ids = fields.Many2many('helpdesk.sla', 'helpdesk_sla_status', 'ticket_id', 'sla_id', string="SLAs", copy=False)
    sla_fail = fields.Boolean("Failed SLA Policy", compute='_compute_sla_fail', search='_search_sla_fail')
    sla_success = fields.Boolean("Success SLA Policy", compute='_compute_sla_success', search='_search_sla_success')
    sla_reached_late = fields.Boolean("Has SLA reached late", compute='_compute_sla_reached_late', compute_sudo=True,
                                      store=True)
    sla_reached = fields.Boolean("Has SLA reached", compute='_compute_sla_reached', compute_sudo=True, store=True)
    ticket_type_id = fields.Many2one('helpdesk.ticket.type', string="Type", tracking=True)

    response_time = fields.Float('SLA Response Time', compute='compute_response_time')
    is_sla_exceeded = fields.Boolean('SLA Exceeded', compute='compute_sla_exceeded')
    balance_time = fields.Float('SLA Remaining Time' ,compute='compute_balance_time')

    @api.depends('sla_ids')
    def compute_response_time(self):
        for rec in self:
            rec.response_time = rec.sla_ids[0].response_time if rec.sla_ids else 0.0

    def is_working_day(self, dt):
        return dt.weekday() not in (5, 6)  # 5=Saturday, 6=Sunday

    def add_sla_hours(self, start_dt, hours):
        tz = pytz.timezone(self.env.user.tz or 'UTC')
        start_dt = pytz.UTC.localize(start_dt).astimezone(tz)
        current_dt = start_dt
        hours_remaining = hours

        WORK_START = time(9, 0)
        WORK_END = time(18, 0)
        BREAK_START = time(13, 0)
        BREAK_END = time(14, 0)

        while hours_remaining > 0:
            if self.is_working_day(current_dt):
                work_start_dt = current_dt.replace(hour=WORK_START.hour, minute=0, second=0, microsecond=0)
                work_end_dt = current_dt.replace(hour=WORK_END.hour, minute=0, second=0, microsecond=0)
                break_start_dt = current_dt.replace(hour=BREAK_START.hour, minute=0)
                break_end_dt = current_dt.replace(hour=BREAK_END.hour, minute=0)

                if current_dt < work_start_dt:
                    current_dt = work_start_dt

                if current_dt >= work_end_dt:
                    current_dt += timedelta(days=1)
                    current_dt = current_dt.replace(hour=WORK_START.hour, minute=0)
                    continue

                available_today = (work_end_dt - current_dt).total_seconds() / 3600.0

                if current_dt < break_end_dt and work_end_dt > break_start_dt:
                    overlap_start = max(current_dt, break_start_dt)
                    overlap_end = min(work_end_dt, break_end_dt)
                    break_overlap = (overlap_end - overlap_start).total_seconds() / 3600.0
                    available_today -= break_overlap

                to_consume = min(hours_remaining, available_today)
                current_dt += timedelta(hours=to_consume)

                if current_dt > break_start_dt and current_dt < break_end_dt:
                    current_dt = break_end_dt

                hours_remaining -= to_consume
            else:
                current_dt += timedelta(days=1)
                current_dt = current_dt.replace(hour=WORK_START.hour, minute=0)

        return current_dt.astimezone(pytz.UTC)

    @api.depends('response_time', 'create_date', 'stage_id')
    def compute_sla_exceeded(self):
        for rec in self:
            is_open = rec.stage_id and rec.stage_id.name.strip().lower() == 'open'

            if not is_open or not rec.response_time or not rec.create_date:
                rec.is_sla_exceeded = False
                continue

            deadline = rec.add_sla_hours(rec.create_date, rec.response_time)
            print(deadline,'deadline')

            now = fields.Datetime.now().replace(tzinfo=None)
            print(now,'now')
            deadline_naive = deadline.replace(tzinfo=None) if deadline.tzinfo else deadline

            rec.is_sla_exceeded = now > deadline_naive

    @api.depends('sla_status_ids.deadline', 'sla_status_ids.reached_datetime')
    def _compute_sla_reached(self):
        sla_status_read_group = self.env['helpdesk.sla.status']._read_group(
            [('exceeded_hours', '<', 0), ('ticket_id', 'in', self.ids)],
            ['ticket_id'],
        )
        sla_status_ids_per_ticket = {ticket.id for [ticket] in sla_status_read_group}
        for ticket in self:
            ticket.sla_reached = ticket.id in sla_status_ids_per_ticket

    @api.depends('sla_status_ids.deadline', 'sla_status_ids.reached_datetime')
    def _compute_sla_reached_late(self):
        """ Required to do it in SQL since we need to compare 2 columns value """
        mapping = {}
        if self.ids:
            self.env.cr.execute("""
                  SELECT ticket_id, COUNT(id) AS reached_late_count
                  FROM helpdesk_sla_status
                  WHERE ticket_id IN %s AND (deadline < reached_datetime OR (deadline < %s AND reached_datetime IS NULL))
                  GROUP BY ticket_id
              """, (tuple(self.ids), fields.Datetime.now()))
            mapping = dict(self.env.cr.fetchall())

        for ticket in self:
            ticket.sla_reached_late = mapping.get(ticket.id, 0) > 0

    @api.depends('sla_status_ids.deadline', 'sla_status_ids.reached_datetime')
    def _compute_sla_deadline(self):
        """ Keep the deadline for the last stage (closed one), so a closed ticket can have a status failed.
            Note: a ticket in a closed stage will probably have no deadline
        """
        now = fields.Datetime.now()
        for ticket in self:
            min_deadline = False
            for status in ticket.sla_status_ids:

                if status.reached_datetime or not status.deadline:
                    continue

                if not min_deadline or status.deadline < min_deadline:
                    min_deadline = status.deadline

            ticket.update({
                'sla_deadline': min_deadline,
                'sla_deadline_hours': ticket.team_id.resource_calendar_id.get_work_duration_data \
                    (now, min_deadline, compute_leaves=True)['hours'] if min_deadline else 0.0,
            })

    @api.depends('sla_deadline')
    def compute_balance_time(self):
        now = fields.Datetime.now()
        for ticket in self:
            calendar = ticket.team_id.resource_calendar_id
            if ticket.sla_deadline and calendar:
                duration_data = calendar.get_work_duration_data(
                    now, ticket.sla_deadline, compute_leaves=True
                )
                ticket.balance_time = duration_data.get('hours', 0.0)
            else:
                ticket.balance_time = 0.0
    @api.depends('sla_deadline', 'sla_reached_late')
    def _compute_sla_fail(self):
        now = fields.Datetime.now()
        for ticket in self:
            if ticket.sla_deadline:
                ticket.sla_fail = (ticket.sla_deadline < now) or ticket.sla_reached_late
            else:
                ticket.sla_fail = ticket.sla_reached_late

    @api.model
    def _search_sla_fail(self, operator, value):
        datetime_now = fields.Datetime.now()
        if (value and operator in expression.NEGATIVE_TERM_OPERATORS) or (
                not value and operator not in expression.NEGATIVE_TERM_OPERATORS):  # is not failed
            return ['&', ('sla_reached_late', '=', False), '|', ('sla_deadline', '=', False),
                    ('sla_deadline', '>=', datetime_now)]
        return ['|', ('sla_reached_late', '=', True), ('sla_deadline', '<', datetime_now)]  # is failed

    @api.depends('sla_deadline', 'sla_reached_late')
    def _compute_sla_success(self):
        now = fields.Datetime.now()
        for ticket in self:
            ticket.sla_success = (ticket.sla_deadline and ticket.sla_deadline > now)

    @api.model
    def _search_sla_success(self, operator, value):
        datetime_now = fields.Datetime.now()
        if (value and operator in expression.NEGATIVE_TERM_OPERATORS) or (
                not value and operator not in expression.NEGATIVE_TERM_OPERATORS):  # is failed
            return [('sla_status_ids.reached_datetime', '>', datetime_now), ('sla_reached_late', '!=', False), '|',
                    ('sla_deadline', '!=', False), ('sla_deadline', '<', datetime_now)]
        return [('sla_status_ids.reached_datetime', '<', datetime_now), ('sla_reached', '=', True),
                ('sla_reached_late', '=', False), '|', ('sla_deadline', '=', False),
                ('sla_deadline', '>=', datetime_now)]  # is success

