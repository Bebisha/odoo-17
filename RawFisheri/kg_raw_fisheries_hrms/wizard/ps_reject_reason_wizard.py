from odoo import models, fields, _
from odoo.exceptions import ValidationError, UserError


class PSRejectReasonWizard(models.TransientModel):
    _name = "ps.reject.reason.wizard"
    _description = "Pending Salary Reject Reason"

    reason = fields.Text(string='Rejection Reason', required=True)
    in_form = fields.Boolean(default=False)

    def action_submit_reject(self):
        from_dashboard = self.env.context.get('from_dashboard', False)
        active_id = self.env.context.get('active_id')
        if not active_id:
            raise ValidationError(_("No record found to reject."))

        record = self.env['pending.salary'].sudo().browse(active_id)

        if self.env.user.id != record.ps_approve_users_id.id:
            raise UserError(_("You have no access to reject"))

        if record.reason_for_reject:
            raise ValidationError(_("This record has already been rejected with a reason."))

        if record.state in ['approved', 'cancel']:
            raise ValidationError(_("This record cannot be rejected in its current state."))

        if not self.reason:
            raise ValidationError(_("Rejection reason is required."))

        record.write({'reason_for_reject': self.reason})
        record.state = 'rejected'

        doc_type = "Pending Salary"

        email_from = record.company_id.email
        manager_name = self.env.user.name
        submitter_name = record.create_uid.name
        submitter_email = record.create_uid.email
        today = fields.Date.today().strftime('%d/%m/%Y')

        subject = _(f"{doc_type} Approval Request Rejected")

        body_html = f'''
              <p>Dear {submitter_name},</p>

              <p>Your {doc_type.lower()} request has been <strong>rejected</strong> by <strong>{manager_name}</strong>.</p>

              <p><strong>Submission Details:</strong></p>
              <ul>
                  <li><strong>Submission Date:</strong> {today}</li>
                  <li><strong>Manager:</strong> {manager_name}</li>
              </ul>

              <p><strong>Rejection Reason:</strong></p>
              <p style="background-color:#f8d7da;padding:10px;border-left:5px solid #f44336;">
                  {self.reason}
              </p>

              <p>If you have any questions or need clarification, please contact your manager directly.</p>

              <p>Best regards,<br/>{manager_name}</p>
          '''

        self.env['mail.mail'].sudo().create({
            'subject': subject,
            'body_html': body_html,
            'email_to': submitter_email,
            'email_from': email_from,
        }).send()

        if not self.in_form:
            if from_dashboard:
                return {'type': 'ir.actions.client', 'tag': 'reload'}
            return {
                'type': 'ir.actions.act_url',
                'url': '/thank-you-template',
                'target': 'self',
            }
