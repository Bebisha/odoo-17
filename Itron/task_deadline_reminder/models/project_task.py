# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Anjhana A K(<https://www.cybrosys.com>)
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import datetime
from datetime import datetime
from odoo import api, fields, models


class ProjectTask(models.Model):
    """inherited to add reminder field"""
    _inherit = "project.task"


    @api.model
    def _cron_deadline_reminder(self):
        """Checks daily , if the task reaches deadline it will send the
        mail to assignee """
        # done_stage = self.env['project.task.type'].search([('name', '=', 'Done')], limit=1)
        # done_stage_id = done_stage.id if done_stage else 0
        task_id = self.search([('date_deadline', '!=', None),
                               ('user_ids', '!=', None)])
                               # ('user_ids', '!=', None),('stage_id', '!=', done_stage_id)])
        today = datetime.now().date()
        for task in task_id:
            reminder_date = task.date_deadline
            if reminder_date == today and task:
                template_id = self.env.ref(
                    'task_deadline_reminder.email_template_deadline_reminder')
                if template_id:
                    email_template_obj = self.env['mail.template'].browse(
                        template_id.id)
                    emails = [user.email for user in task.user_ids]
                    email_to = ', '.join(emails)
                    email_values = {
                        'email_to': email_to,
                        'email_cc': False,
                        'scheduled_date': False,
                        'recipient_ids': [],
                        'partner_ids': [],
                        'auto_delete': True,
                    }
                    email_template_obj.send_mail(
                        task.id, force_send=True, email_values=email_values)
        return True
