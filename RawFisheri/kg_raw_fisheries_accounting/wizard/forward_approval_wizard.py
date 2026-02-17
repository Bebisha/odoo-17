from odoo import models, fields, _
from odoo.exceptions import ValidationError


class ForwardApprovalWizard(models.TransientModel):
    _name = "forward.approval.wizard"
    _description = "Forward Approval Wizard"

    def default_move_id(self):
        active_id = self.env.context.get('active_id')
        record = self.env['account.move'].sudo().browse(active_id)
        return record.id

    def default_current_user_id(self):
        active_id = self.env.context.get('active_id')
        record = self.env['account.move'].sudo().browse(active_id)
        is_final = record.need_final_approve and record.waiting_final_approve
        current_user_id = record.first_final_approve_user_id if is_final else record.first_approve_user_id
        return current_user_id

    def default_users(self):
        active_id = self.env.context.get('active_id')
        record = self.env['account.move'].sudo().browse(active_id)
        is_final = record.need_final_approve and record.waiting_final_approve
        if record.move_type == 'out_invoice':
            users = record.default_inv_final_approve_users_ids if is_final else record.default_inv_approve_users_ids
        else:
            users = record.default_bill_final_approve_users_ids if is_final else record.default_bill_approve_users_ids
        users_ids = [(6, 0, users.ids)]
        return users_ids

    name = fields.Char(string="Reference")
    current_user_id = fields.Many2one("res.users", string="Current User", default=default_current_user_id)
    move_id = fields.Many2one("account.move", string="Move", default=default_move_id)
    user_ids = fields.Many2many("res.users", string="Approve Users", default=default_users)
    forward_user_id = fields.Many2one("res.users", string="Forward User")
    is_final_approve = fields.Boolean(default=False, string="Is Final Approve")

    def action_forward(self):
        if self.is_final_approve:
            if self.current_user_id != self.env.user:
                raise ValidationError("You do not have access to change the approved user")

            if self.move_id.state in ['approved', 'posted', 'cancel']:
                raise ValidationError(_("This record cannot be forward in its current state."))

            is_final = self.move_id.need_final_approve and self.move_id.waiting_final_approve
            is_in_invoice = self.move_id.move_type == 'in_invoice'

            if is_final:
                if is_in_invoice:
                    self.move_id.bill_final_approve_user_id = self.forward_user_id.id
                else:
                    self.move_id.inv_final_approve_user_id = self.forward_user_id.id
            else:
                if is_in_invoice:
                    self.move_id.bill_approve_user_id = self.forward_user_id.id
                else:
                    self.move_id.inv_approve_user_id = self.forward_user_id.id

            self.move_id.action_forwarding_approval()
        else:
            if self.current_user_id != self.env.user:
                raise ValidationError("You do not have access to change the approved user")

            if self.move_id.need_final_approve:
                if self.move_id.waiting_final_approve:
                    raise ValidationError(_("This record cannot be forward in its current state."))
            else:
                if self.move_id.state in ['approved', 'posted', 'cancel']:
                    raise ValidationError(_("This record cannot be forward in its current state."))

            is_final = self.move_id.need_final_approve and self.move_id.waiting_final_approve
            is_in_invoice = self.move_id.move_type == 'in_invoice'

            if is_final:
                if is_in_invoice:
                    self.move_id.bill_final_approve_user_id = self.forward_user_id.id
                else:
                    self.move_id.inv_final_approve_user_id = self.forward_user_id.id
            else:
                if is_in_invoice:
                    self.move_id.bill_approve_user_id = self.forward_user_id.id
                else:
                    self.move_id.inv_approve_user_id = self.forward_user_id.id

            self.move_id.action_forwarding_approval()
