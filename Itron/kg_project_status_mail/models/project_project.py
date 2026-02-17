# -*- coding: utf-8 -*-
from datetime import date, timedelta

from odoo import models, fields


class ProjectTaskType(models.Model):
    _inherit = 'project.project'

    is_amc = fields.Boolean('Is AMC', related='stage_id.is_amc')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')

    def amc_expiry_notification(self):
        for i in self.search([]):
            end_date = i.end_date
            today = date.today()
            if i.end_date:
                days_30_before = end_date + timedelta(days=-30)
                days_15_before = end_date + timedelta(days=-15)

                if days_30_before == today or days_15_before == today:
                    group_au = self.env.ref('account.group_account_user')
                    map_pm_users_mail = [i.user_id.login]
                    map_au_users_mail = group_au.users.mapped('partner_id').mapped('email')
                    emails = map_pm_users_mail + map_au_users_mail
                    users_mail = ",".join(emails)
                    email_values = {
                        'email_to': users_mail,
                        'email_from': self.env.user.email_formatted,
                        'author_id': self.env.user.partner_id.id,
                    }
                    mail_template = self.env.ref('kg_project_status_mail.project_expiry_status_mail_template')
                    mail_template.sudo().send_mail(i.id, force_send=True, email_values=email_values)
