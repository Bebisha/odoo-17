# -*- coding:utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from odoo.tools import float_round


class TimeSheetEntry(models.TransientModel):
    _name = 'wizard.timesheet.entry'
    _description = 'Time Sheet Entry'

    sale_id = fields.Many2one('sale.order', string='Job Order')
    project_id = fields.Many2one('project.project', string='Project', domain="[('sale_order_id', '=', sale_id)]")
    task_id = fields.Many2one('project.task', string='Scope', domain="[('project_id', '=', project_id), ('parent_id', '=', False)]")
    team_id = fields.Many2one('project.team', string='Team', related='project_id.project_team_id')
    team_member_ids = fields.Many2many('hr.employee', string='Team Members', domain=[('staff_worker', '=', 'technical')])
    type = fields.Selection([('time_in', 'Time In'), ('time_out', 'Time Out')], string='Entry Type', required=1)
    time_in = fields.Datetime(string='Time In')
    time_out = fields.Datetime(string='Time Out')
    entry_lines = fields.One2many('time.entry.line', 'timesheet_entry_id', string='Entry Lines')

    anchorage = fields.Boolean(string="Anchorage", default=False)
    overseas = fields.Boolean(string="Overseas", default=False)

    @api.onchange('anchorage', )
    def onchange_parent_flags(self):
        if self.anchorage:
            self.overseas = False
        for line in self.entry_lines:
            line.anchorage = self.anchorage


    @api.onchange('overseas' )
    def onchange_overseas_flags(self):
        if self.overseas:
            self.anchorage = False
        for line in self.entry_lines:
            line.overseas = self.overseas


    # def write(self, vals):
    #     res = super().write(vals)
    #     if 'anchorage' in vals or 'overseas' in vals:
    #         for rec in self:
    #             rec.entry_lines.write({
    #                 'anchorage': rec.anchorage,
    #                 'overseas': rec.overseas,
    #             })
    #     return res



    @api.onchange('team_id')
    def onchange_team(self):
        """ Listing all team members coming under team """
        team_members = self.team_id.team_member_ids
        self.team_member_ids = [(6, 0, team_members.ids)]

    @api.onchange('time_in')
    def onchange_time_in(self):
        """Update time_in in entry lines when main time_in changes"""
        if self.entry_lines:
            for line in self.entry_lines:
                line.time_in = self.time_in

    @api.onchange('type')
    def load_lines(self):
        lines = []
        self.entry_lines = False
        if self.type == 'time_in':
            for user in self.team_member_ids:
                lines.append((0, 0, {
                    'assignee_id': user.id,
                    'time_in': self.time_in,
                }))
            self.entry_lines = lines

    def _get_employee_work_hours(self, employee, start_dt, end_dt):
        if not employee or not employee.resource_calendar_id:
            return 0.0

        calendar = employee.resource_calendar_id
        print(calendar,'calendere')
        working_hours = employee.resource_calendar_id.hours_per_day
        print(working_hours,'workingggggggggggggg')

        print(calendar.get_work_hours_count(start_dt, end_dt),'calendar.get_work_hours_count(start_dt, end_dt)')
        return working_hours

    @api.onchange('time_out')
    def onchange_time_out(self):
        if not self.time_out or not self.team_member_ids:
            return

        self.entry_lines = [(5, 0, 0)]

        date = self.time_out.date()

        timesheets = self.env['account.analytic.line'].sudo().search([
            ('employee_id', 'in', self.team_member_ids.ids),
            ('date', '=', date),
            ('time_in', '!=', False),
            ('time_out', '=', False),
        ])

        lines = []
        for ts in timesheets:
            time_in = ts.time_in
            time_out = self.time_out
            employee = ts.employee_id

            total_hours = 0.0
            normal_hours = 0.0
            ot_hours = 0.0

            if time_in and time_out:
                delta = time_out - time_in
                total_hours = delta.total_seconds() / 3600.0

                work_hours = self._get_employee_work_hours(
                    employee, time_in, time_out
                )
                print(work_hours,'ooooooooooooooo')

                if total_hours > work_hours:
                    normal_hours = work_hours
                    ot_hours = total_hours - work_hours
                else:
                    normal_hours = total_hours
                    ot_hours = 0.0

            lines.append((0, 0, {
                'assignee_id': ts.employee_id.id,
                'subtask_id': ts.task_id.id,
                'timesheet_id': ts.id,
                'time_in': time_in,
                'time_out': time_out,
                'total_hours': float_round(total_hours, 2),
                'normal_hours': float_round(normal_hours, 2),
                'ot_hours': float_round(ot_hours, 2),
                'overseas': ts.overseas,
                'anchorage': ts.anchorage,
            }))

        self.entry_lines = lines



    def action_submit(self):
        AnalyticLine = self.env['account.analytic.line']

        invalid_time_out_lines = []
        if self.type == 'time_out' :
            for line in self.entry_lines:

                time_in = line.time_in
                time_out = line.time_out
                if not time_out:
                    invalid_time_out_lines.append(line)
                    continue
                if time_in and time_out:

                    if time_in.date() != time_out.date():
                        invalid_time_out_lines.append(line)
                        continue

                    if time_out <= time_in:
                        invalid_time_out_lines.append(line)
                        continue

                    line.timesheet_id.write({
                    'time_out': line.time_out,
                    'normal_hours': line.normal_hours,
                    'ot_hours': line.ot_hours,
                    'anchorage': line.anchorage,
                    'overseas': line.overseas,
                })


        elif self.type == 'time_in':
            entry_date = (self.time_in or fields.Datetime.now()).date()
            duplicate_lines = []

            for line in self.entry_lines:

                existing_ts = AnalyticLine.search([
                    ('user_id', '=', line.assignee_id.id),
                    ('date', '=', entry_date),
                ], limit=1)

                if existing_ts:
                    duplicate_lines.append(line.id)
                    continue

                AnalyticLine.create({
                    'name': self.task_id.name,
                    'project_id': self.project_id.id,
                    'task_id': line.subtask_id.id,
                    'employee_id': line.assignee_id.id,
                    'date': entry_date,
                    'time_in': line.time_in,
                    'overseas': line.overseas,
                    'anchorage': line.anchorage,
                    'unit_amount': line.total_hours,
                })
            print(duplicate_lines)
            if duplicate_lines:
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Duplicate Timesheets Found',
                    'res_model': 'timesheet.confirm.wizard',
                    'view_mode': 'form',
                    'target': 'new',
                    'context': {
                        'default_duplicate_line_ids': [(6, 0, duplicate_lines)],
                        'default_project_id': self.project_id.id,
                        'default_date': entry_date,
                    }
                }
        print(invalid_time_out_lines,'pppppppppppp')

        if invalid_time_out_lines:

            raise ValidationError(
                "Time Out Is Invalid!!"
            )


class TimeSheetWizardLines(models.TransientModel):
    _name = 'time.entry.line'
    _description = 'Time Sheet Wizard Lines'

    assignee_id = fields.Many2one('hr.employee', string='Assignee')
    subtask_id = fields.Many2one('project.task', string='Subtask')
    timesheet_entry_id = fields.Many2one('wizard.timesheet.entry', string='Timesheet Entry')
    timesheet_id = fields.Many2one('account.analytic.line', string='Timesheet')
    time_in = fields.Datetime(string='Time In')
    time_out = fields.Datetime(string='Time Out')
    total_hours = fields.Float(string='Total Hours')
    normal_hours = fields.Float(string='Normal Hours')
    ot_hours = fields.Float(string='OT')
    # anchorage = fields.Boolean(related='timesheet_entry_id.anchorage', store=True,readonly=False)
    # overseas = fields.Boolean(related='timesheet_entry_id.overseas', store=True)
    travel = fields.Boolean(string="Travel", default=False)

    anchorage = fields.Boolean(
        # compute='_compute_flags',
        # inverse='_inverse_anchorage',
    )

    overseas = fields.Boolean(
        # compute='_compute_flags',
        # inverse='_inverse_overseas',
    )

    # @api.depends('timesheet_entry_id.anchorage', 'timesheet_entry_id.overseas')
    # def _compute_flags(self):
    #     for line in self:
    #         if line.timesheet_entry_id.anchorage == True:
    #             print(line,'ppppppppppppppppppppppppppp')
    #
    #             line.anchorage = True
    #         else:
    #             line.anchorage = False
    #         if line.timesheet_entry_id.overseas == True:
    #
    #             line.overseas = True
    #         else:
    #             line.overseas = False
    #
    # def _inverse_anchorage(self):
    #     pass
    #
    # def _inverse_overseas(self):
    #     pass

    def _get_employee_work_hours(self, employee, start_dt, end_dt):
        if not employee or not employee.resource_calendar_id:
            return 0.0
        working_hours = employee.resource_calendar_id.hours_per_day
        print(working_hours, 'workingggggggggggggg')
        return working_hours

    @api.onchange('anchorage', )
    def onchange_parent_flags(self):
        if self.anchorage:
            self.overseas = False

    @api.onchange('overseas')
    def onchange_overseas_flags(self):
        if self.overseas:
            self.anchorage = False

    @api.onchange('time_in', 'time_out')
    def onchange_time_out_calculation(self):
        for line in self:
            if not line.time_in or not line.time_out or not line.assignee_id:
                line.total_hours = 0.0
                line.normal_hours = 0.0
                line.ot_hours = 0.0
                continue

            if line.time_out <= line.time_in:
                line.total_hours = 0.0
                line.normal_hours = 0.0
                line.ot_hours = 0.0
                return

            delta = line.time_out - line.time_in
            total_hours = delta.total_seconds() / 3600.0

            work_hours = line._get_employee_work_hours(
                line.assignee_id, line.time_in, line.time_out
            )
            print(work_hours,'workhours_loal')

            if total_hours > work_hours:
                normal_hours = work_hours
                ot_hours = total_hours - work_hours
            else:
                normal_hours = total_hours
                ot_hours = 0.0

            line.total_hours = float_round(total_hours, 2)
            line.normal_hours = float_round(normal_hours, 2)
            line.ot_hours = float_round(ot_hours, 2)


