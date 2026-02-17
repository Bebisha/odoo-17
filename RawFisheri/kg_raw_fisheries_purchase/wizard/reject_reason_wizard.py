from odoo import models, fields, _
from odoo.exceptions import ValidationError, UserError


class PORejectReasonWizard(models.TransientModel):
    _name = 'po.reject.reason.wizard'
    _description = 'Purchase Rejection Reason Wizard'

    reason = fields.Text(string='Rejection Reason', required=True)
    in_form = fields.Boolean(default=False)
    po_id = fields.Many2one("purchase.entry",string="Purchase Order")

    def action_submit_reject(self):
        # return
        # if self.is_final_approve:
        #     from_dashboard = self.env.context.get('from_dashboard', False)
        #
        #     if self.approval_id:
        #         active_id = self.approval_id.move_id.id
        #     elif self.account_move_id:
        #         account_move_id = self.env['account.move'].search([('id', '=', self.account_move_id)], limit=1)
        #         active_id = account_move_id.id
        #     else:
            active_id = self.env.context.get('active_id')
        #
            if not active_id:
                raise ValidationError(_("No record found to reject."))

            record = self.env['purchase.entry'].sudo().browse(active_id)
        #
        #     if record.move_type == 'in_invoice':
        #         if self.env.user.id != record.bill_final_approve_user_id.id:
        #             raise UserError(_("You have no access to reject"))
        #
        #     if record.move_type == 'out_invoice':
        #         if self.env.user.id != record.inv_final_approve_user_id.id:
        #             raise UserError(_("You have no access to reject"))
        #
            if record.state == 'rejected':
                raise ValidationError(_("This record has already been rejected with a reason."))

            if record.state in ['approved', 'draft', 'cancel']:
                raise ValidationError(_("This record cannot be rejected in its current state."))

            if not self.reason:
                raise ValidationError(_("Rejection reason is required."))

            record.write({'reject_reason': self.reason})
            record.state = 'rejected'
        #
        #     doc_type = "Vendor Bill" if record.move_type == 'in_invoice' else "Invoice"
        #
        #     email_from = record.company_id.email
        #     manager_name = self.env.user.name
        #     submitter_name = record.create_uid.name
        #     submitter_email = record.create_uid.email
        #     today = fields.Date.today().strftime('%d/%m/%Y')
        #
        #     subject = _(f"{doc_type} Final Approval Request Rejected")
        #
        #     body_html = f'''
        #                     <p>Dear {submitter_name},</p>
        #
        #                     <p>Your {doc_type.lower()} request has been <strong>rejected</strong> by <strong>{manager_name}</strong>.</p>
        #
        #                     <p><strong>Submission Details:</strong></p>
        #                     <ul>
        #                         <li><strong>Submission Date:</strong> {today}</li>
        #                         <li><strong>Manager:</strong> {manager_name}</li>
        #                     </ul>
        #
        #                     <p><strong>Rejection Reason:</strong></p>
        #                     <p style="background-color:#f8d7da;padding:10px;border-left:5px solid #f44336;">
        #                         {self.reason}
        #                     </p>
        #
        #                     <p>If you have any questions or need clarification, please contact your manager directly.</p>
        #
        #                     <p>Best regards,<br/>{manager_name}</p>
        #                 '''
        #
        #     self.env['mail.mail'].sudo().create({
        #         'subject': subject,
        #         'body_html': body_html,
        #         'email_to': submitter_email,
        #         'email_from': email_from,
        #     }).send()
        #
        #     if self.approval_id:
        #         self.approval_id.action_refuse()
        #     else:
        #         record.approval_id.action_refuse()
        #
        #     if record.final_approval_id:
        #         record.final_approval_id.action_refuse()
        #
        #     if not self.in_form:
        #         if from_dashboard:
        #             return {'type': 'ir.actions.client', 'tag': 'reload'}
        #         return {
        #             'type': 'ir.actions.act_url',
        #             'url': '/thank-you-template',
        #             'target': 'self',
        #         }
        # else:
        #     from_dashboard = self.env.context.get('from_dashboard', False)
        #
        #     if self.approval_id:
        #         active_id = self.approval_id.move_id.id
        #     elif self.account_move_id:
        #         account_move_id = self.env['account.move'].search([('id', '=', self.account_move_id)], limit=1)
        #         active_id = account_move_id.id
        #     else:
        #         active_id = self.env.context.get('active_id')
        #
        #     if not active_id:
        #         raise ValidationError(_("No record found to reject."))
        #
        #     record = self.env['account.move'].sudo().browse(active_id)
        #
        #     if record.move_type == 'in_invoice':
        #         if self.env.user.id != record.bill_approve_user_id.id:
        #             raise UserError(_("You have no access to reject"))
        #
        #     if record.move_type == 'out_invoice':
        #         if self.env.user.id != record.inv_approve_user_id.id:
        #             raise UserError(_("You have no access to reject"))
        #
        #     if record.state == 'rejected':
        #         raise ValidationError(_("This record has already been rejected with a reason."))
        #
        #     if record.need_final_approve:
        #         if record.waiting_final_approve:
        #             raise ValidationError(_("This record cannot be rejected in its current state."))
        #     else:
        #         if record.state in ['approved', 'posted', 'cancel']:
        #             raise ValidationError(_("This record cannot be rejected in its current state."))
        #
        #     if not self.reason:
        #         raise ValidationError(_("Rejection reason is required."))
        #
        #     record.write({'reason_for_reject': self.reason})
        #     record.state = 'rejected'
        #
        #     doc_type = "Vendor Bill" if record.move_type == 'in_invoice' else "Invoice"
        #
        #     email_from = record.company_id.email
        #     manager_name = self.env.user.name
        #     submitter_name = record.create_uid.name
        #     submitter_email = record.create_uid.email
        #     today = fields.Date.today().strftime('%d/%m/%Y')
        #
        #     subject = _(f"{doc_type} Approval Request Rejected")
        #
        #     body_html = f'''
        #         <p>Dear {submitter_name},</p>
        #
        #         <p>Your {doc_type.lower()} request has been <strong>rejected</strong> by <strong>{manager_name}</strong>.</p>
        #
        #         <p><strong>Submission Details:</strong></p>
        #         <ul>
        #             <li><strong>Submission Date:</strong> {today}</li>
        #             <li><strong>Manager:</strong> {manager_name}</li>
        #         </ul>
        #
        #         <p><strong>Rejection Reason:</strong></p>
        #         <p style="background-color:#f8d7da;padding:10px;border-left:5px solid #f44336;">
        #             {self.reason}
        #         </p>
        #
        #         <p>If you have any questions or need clarification, please contact your manager directly.</p>
        #
        #         <p>Best regards,<br/>{manager_name}</p>
        #     '''
        #
        #     self.env['mail.mail'].sudo().create({
        #         'subject': subject,
        #         'body_html': body_html,
        #         'email_to': submitter_email,
        #         'email_from': email_from,
        #     }).send()
        #
        #     if self.approval_id:
        #         self.approval_id.action_refuse()
        #     else:
        #         record.approval_id.action_refuse()
        #
        #     if not self.in_form:
        #         if from_dashboard:
        #             return {'type': 'ir.actions.client', 'tag': 'reload'}
        #         return {
        #             'type': 'ir.actions.act_url',
        #             'url': '/thank-you-template',
        #             'target': 'self',
        #         }
