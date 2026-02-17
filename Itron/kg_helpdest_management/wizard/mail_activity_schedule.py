# -*- coding: utf-8 -*-
from odoo import models, fields, _


class MailActivitySchedule(models.TransientModel):
    _inherit = 'mail.activity.schedule'

    helpdesk_id = fields.Many2one('helpdesk.ticket', string='Helpdesk', readonly=True, copy=False)
    planned_hours = fields.Float(string='Planned Hours', required=True)

    def _action_schedule_activities(self):
        if self._context.get('active_model') == 'helpdesk.ticket':
            if not self.helpdesk_id.stage_id.in_progress:
                stage = self.env['helpdesk.ticket.stage'].search(
                    [('in_progress', '=', True)], limit=1)
                self.helpdesk_id.stage_id = stage.id
            return self._get_applied_on_records().activity_schedule(
                activity_type_id=self.activity_type_id.id,
                automated=False,
                summary=self.summary,
                note=self.note,
                user_id=self.activity_user_id.id,
                date_deadline=self.date_deadline,
                helpdesk_id=self.helpdesk_id.id,
                planned_hrs=self.planned_hours,
                stage='in_progress'
            )
        else:
            return self._get_applied_on_records().activity_schedule(
                activity_type_id=self.activity_type_id.id,
                automated=False,
                summary=self.summary,
                note=self.note,
                user_id=self.activity_user_id.id,
                date_deadline=self.date_deadline
            )
