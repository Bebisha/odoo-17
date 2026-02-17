# -*- coding: utf-8 -*-

from datetime import datetime

from odoo import models, fields, tools, _, api, Command
from odoo.exceptions import ValidationError


class ProjectContractRequest(models.Model):
    _name = 'project.reject.reason'

    reason = fields.Text('Reason For Rejection')

    resource_id = fields.Many2one('project.resource.pool')

    def reject_button(self):
        """reject button for Resource"""
        if self.reason:
            self.resource_id.write({
                'is_reject': True,
                'state': 'reject',
                'reject_res': self.reason
            })

            # Get the email address of the resource's creator
            creator_email = self.resource_id.users_id.email

            # Add the creator's email address to the list of recipients
            group_send_mail = [creator_email]

            subject = _('Resource Request Rejected for: %s') % self.resource_id.users_id.name

            body = _('Resource request has been rejected!!')

            mail_values = {
                'subject': subject,
                'body': body,
                'email_to': ', '.join(group_send_mail),
            }

            # Send the email
            self.env['mail.mail'].create(mail_values).send()
            for rec in self.resource_id.task_ids:
                if rec.task_id:
                    # ll
                    rec.planned_hrs -= rec.extend_hrs
                if rec.ext_bool:
                    rec.unlink()
            from_dashboard = self.env.context.get('from_dashboard', False)
            if from_dashboard:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'reload',
                }
        else:
            raise ValidationError('Add a Reason for reject !!!')
