# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class RejectReasonWizard(models.TransientModel):
    _name = 'reject.reason.wizard'
    _description = 'Rejection Reason Wizard'

    reason = fields.Text(string='Rejection Reason', required=True)

    def action_submit_reject(self):
        """ Submit the rejection reason and send a rejection email """
        from_dashboard = self.env.context.get('from_dashboard', False)
        active_id = self.env.context.get('active_id')
        if not active_id:
            raise ValidationError("No record found to reject.")

        record = self.env['early.late.request'].sudo().browse(active_id)

        if record.reason_for_return:
            raise ValidationError("This record has already been rejected with a reason.")

        if record.state in ['lm_approved', 'cancel']:
            raise ValidationError("This record cannot be rejected in its current state.")

        record.write({'reason_for_return': self.reason})
        record.action_reject()

        outgoing_mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
        email_from = outgoing_mail_server.smtp_user
        manager_name = self.env.user.name
        email_details = {
            'subject': '',
            'reason_label': '',
        }
        if record.type == 'early_departure':
            email_details['subject'] = _('Early Departure Request Returned')
            email_details['reason_label'] = _('Reason for Early Departure')
        else:
            email_details['subject'] = _('Late Arrival Request Returned')
            email_details['reason_label'] = _('Reason for Late Arrival')

        body_html = f'''
            <div>Dear {record.employee_id.name},</div>
            <br/>
            <div>We regret to inform you that your submitted <strong>{record.type.replace('_', ' ').title()} request</strong> has been <strong>rejected</strong> by your manager.</div>
            <br/>
            <div><strong>Details:</strong></div>
            <ul>
                <li><strong>Submission Date:</strong> {fields.Date.today()}</li>
                <li><strong>{email_details["reason_label"]}:</strong> {record.reason}</li>
                <li><strong>Manager:</strong> {manager_name}</li>
            </ul>
            <br/>
            <div><strong>Rejection Reason:</strong></div>
            <div>{record.reason_for_return}</div>
            <br/>
            <p>If you have any questions or require clarification, please contact your manager directly.</p>
            <br/>
            <p>Best regards,</p>
            <p>Your HR Team</p>
            <div>{manager_name}</div>
        '''
        mail_values = {
            'subject': email_details['subject'],
            'body_html': body_html,
            'email_to': record.employee_id.work_email,
            'email_from': email_from,
        }
        self.env['mail.mail'].sudo().create(mail_values).send()
        if from_dashboard:
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
        return {
            'type': 'ir.actions.act_url',
            'url': '/thank-you-template',
            'target': 'self',
        }