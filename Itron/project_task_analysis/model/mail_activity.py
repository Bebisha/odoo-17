from odoo import models, fields, api, _
from datetime import date, timedelta
import logging

from odoo.exceptions import ValidationError
from odoo.tools import get_lang, is_html_empty


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    def action_notify(self):
        if not self:
            return
        for activity in self:
            if activity.user_id.lang:
                activity = activity.with_context(lang=activity.user_id.lang)

            model_description = activity.env['ir.model']._get(activity.res_model).display_name
            record = activity.env[activity.res_model].browse(activity.res_id)
            employee_names = ''
            if activity.res_model == 'hr.leave':
                employee_names = ', '.join(record.employee_ids.mapped('name'))
            body = activity.env['ir.qweb']._render(
                'mail.message_activity_assigned',
                {
                    'activity': activity,
                    'model_description': model_description,
                    'is_html_empty': is_html_empty,
                    'employee': employee_names
                },
                minimal_qcontext=True
            )
            outgoing_mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
            if activity.user_id:
                record.message_notify(
                    partner_ids=activity.user_id.partner_id.ids,
                    body=body,
                    email_from=outgoing_mail_server.sudo().smtp_user,
                    record_name=activity.res_name,
                    model_description=model_description,
                    email_layout_xmlid='mail.mail_notification_layout',
                    subject=_('"%(activity_name)s: %(summary)s" assigned to you',
                              activity_name=activity.res_name,
                              summary=activity.summary or activity.activity_type_id.name),
                    subtitles=[_('Activity: %s', activity.activity_type_id.name),
                               _('Deadline: %s', activity.date_deadline.strftime(get_lang(activity.env).date_format))]
                )