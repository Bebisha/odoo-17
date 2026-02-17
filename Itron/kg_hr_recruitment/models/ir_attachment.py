# -*- encoding: utf-8 -*-
from odoo import api, models


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    @api.model
    def create(self, vals):
        """ supering create function """
        result = super(IrAttachment, self).create(vals)
        if result.res_model == 'hr.applicant':
            result._send_application_email()
        return result

    def _send_application_email(self):
        """ function send application email """
        for record in self:
            application = self.env['hr.applicant'].sudo().browse(record.res_id)
            if not application:
                return

            if not application.send_email:
                body_html = (f"Dear Recruitment Team,<br/><br/>We have received a new job application. "
                             f"Below are the applicant's details for your reference:<br/><br/>"
                             f"<b>Applicant Name:</b> {application.partner_name}<br/>"
                             f"<b>Position Applied For:</b> {application.job_id.name}<br/>"
                             f"<b>Email:</b> {application.email_from}<br/>"
                             f"<b>Phone Number:</b> {application.partner_phone}<br/><br/>"
                             f"The applicant has provided their resume (attached to this email). Please review the application "
                             f"and take the necessary steps to process it.<br/><br/>"
                             f"If further details or actions are required, kindly reach out to the applicant directly or update "
                             f"the recruitment system with the next steps.<br/><br/>"
                             f"<b>Let’s work together to ensure a seamless recruitment process!</b><br/><br/><br/>"
                             f"Best regards,<br/><br/>")

                email_values = {
                    'subject': f"New Job Application: {application.job_id.name}",
                    'body_html': body_html,
                    'email_from': 'itron@klystronglobal.com',
                    'email_to': application.job_id.email_to,
                    'attachment_ids': [(6, 0, record.ids)],
                }
                email = self.env['mail.mail'].sudo().create(email_values)
                email.send()
                application.send_email = True
