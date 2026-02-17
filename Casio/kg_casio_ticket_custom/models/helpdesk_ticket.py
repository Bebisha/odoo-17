# -*- coding: utf-8 -*-
from odoo import fields, models, api
from datetime import date, datetime, time

from odoo.api import onchange
import pytz
from pytz import timezone, UTC


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    check_date_stage = fields.Datetime(string='Reply Time', readonly=True, copy=False)
    is_replied = fields.Boolean(string='Is Replied', default=False, copy=False, related='stage_id.is_replied')
    reply_date = fields.Date(string='Reply Date', readonly=True, copy=False,)

    @onchange('stage_id')
    def onchange_stage_id(self):
        """ function on change to get the time in which stage is changed """
        for ticket in self:
            if ticket.stage_id:
                ticket.check_date_stage = fields.Datetime.now()

    @api.depends('team_id', 'message_ids')
    def _compute_user_and_stage_ids(self):
        incoming_subtype_id = self.env.ref('mail.mt_comment').id
        replied_stage = self.env['helpdesk.stage'].search([('is_replied', '=', True)])
        for ticket in self.filtered(lambda ticket: ticket.team_id):
            if not ticket.check_date_stage:
                ticket.write({'check_date_stage': ticket.create_date})
            previous_stage = ticket._origin.stage_id
            if not ticket.user_id:
                ticket.user_id = ticket.team_id._determine_user_to_assign()[ticket.team_id.id]
            if not ticket.stage_id or ticket.stage_id not in ticket.team_id.stage_ids:
                ticket.stage_id = ticket.team_id._determine_stage()[ticket.team_id.id]
            if ticket.message_ids:
                messages = self.env['mail.message'].search([
                    ('model', '=', 'helpdesk.ticket'),
                    ('res_id', '=', ticket.id),
                    ('message_type', '=', 'email'),
                    ('subtype_id', '=', incoming_subtype_id)
                ])
                if messages and replied_stage:
                    last_message = max(messages, key=lambda msg: msg.create_date)
                    message_time = last_message.create_date
                    if message_time:
                        ticket.write({'reply_date': message_time})
                    message_time_local_tz = pytz.timezone(ticket.user_id.tz or 'UTC')
                    message_time_local = message_time.replace(tzinfo=UTC).astimezone(message_time_local_tz)

                    if previous_stage:
                        if ticket.check_date_stage:
                            if ticket.check_date_stage.tzinfo is None:
                                check_date_stage = pytz.utc.localize(ticket.check_date_stage).astimezone(
                                    message_time_local_tz)
                            if message_time_local > check_date_stage:
                                ticket.sudo().write({'stage_id': replied_stage.id})


class HelpdeskStage(models.Model):
    _inherit = 'helpdesk.stage'

    is_replied = fields.Boolean(string='Is Replied', default=False, copy=False)
    is_new = fields.Boolean(string='Is New', default=False, copy=False)
    is_in_progress = fields.Boolean(string='Is In Progress', default=False, copy=False)
    is_solved = fields.Boolean(string='Is Solved', default=False, copy=False)
    is_cancel = fields.Boolean(string='Is Cancel', default=False, copy=False)
