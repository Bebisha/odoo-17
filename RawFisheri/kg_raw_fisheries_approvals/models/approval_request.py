from odoo import models, fields, api


class KGApprovalRequest(models.Model):
    _inherit = "approval.request"

    move_id = fields.Many2one("account.move", string="Invoice/Bill Ref", copy=False)
    refuse_reason = fields.Char(string="Refuse Reason", copy=False)
    currency_id = fields.Many2one('res.currency', related='move_id.currency_id')
    amount = fields.Monetary(string="Amount", related="move_id.amount_total", currency_field="currency_id")
    vendor_id = fields.Many2one("res.partner", string="Customer/Vendor", related="move_id.partner_id")
    approve_users_ids = fields.Many2many("res.users", string="Approver(s)", compute="compute_approve_users", store=True)

    def compute_approve_users(self):
        for rec in self:
            rec.approve_users_ids = False
            if rec.approver_ids:
                users = rec.approver_ids.mapped('user_id')
                if users:
                    rec.approve_users_ids = [(6, 0, users.ids)]

    def action_approve(self, approver=None):
        res = super(KGApprovalRequest, self).action_approve(approver)

        if self.move_id.need_final_approve:
            if self.move_id.state != 'approved':
                if not self.move_id.waiting_final_approve:
                    self.move_id._action_approve_internal()
                else:
                    self.move_id._action_final_approve_internal()
        else:
            if self.move_id.state != 'approved':
                self.move_id._action_approve_internal()

        return res

    def action_reject(self):
        context = {
            'default_in_form': True,
            'default_approval_id': self.id,
        }

        if self.move_id.need_final_approve and self.move_id.waiting_final_approve:
            context['default_is_final_approve'] = True

        return {
            'name': 'Reject Reason',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'reject.reason.wizard',
            'target': 'new',
            'context': context,
        }

    def action_forward(self):
        ctx = {
            'default_move_id': self.move_id.id if self.move_id else False,
            'default_current_user_id': self.env.user.id,
        }

        if self.move_id.waiting_final_approve:
            ctx['default_is_final_approve'] = True

        return {
            'name': 'Approval Forward',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'forward.approval.wizard',
            'target': 'new',
            'context': ctx,
        }
