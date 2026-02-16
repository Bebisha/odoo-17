from odoo import models, fields, api, exceptions


class UpdatePaymentCheque(models.TransientModel):
    _name = 'update.payment.cheque'

    account_payment_id = fields.Many2one('account.payment')
    current_cheque_leaf_id = fields.Many2one('cheque.leaf.line', string="Current Cheque Leaf", readonly=True)
    new_cheque_leaf_id = fields.Many2one('cheque.leaf.line', string="New Cheque Leaf", required=True)
    cheque_series = fields.Many2one('cheque.leaf', required=True, string="Cheque Book", domain=[('state', '=', 'confirm')])
    cancel_cheque = fields.Boolean(string="Cancel Cheque?")

    def update_cheque_leaf(self):
        if self.cancel_cheque:
            self.current_cheque_leaf_id.status = 'cancel'
            self.current_cheque_leaf_id.account_payment_id = False
        else:
            self.current_cheque_leaf_id.status = 'draft'
            self.current_cheque_leaf_id.account_payment_id = False
        self.new_cheque_leaf_id.status = 'issued'
        self.new_cheque_leaf_id.account_payment_id = self.account_payment_id.id
        self.account_payment_id.cheque_leaf_no = self.new_cheque_leaf_id.id

    @api.onchange('cheque_series')
    def _onchange_cheque_series_wizard(self):
        available_cheque_leaf = []
        if self.cheque_series:
            available_cheque_leaf = self.cheque_series.cheque_leaf_line_ids.filtered(lambda x: x.status == 'draft').ids
            if self.current_cheque_leaf_id.id in available_cheque_leaf:
                available_cheque_leaf.remove(self.current_cheque_leaf_id.id)

        return {
            'domain': {
                'new_cheque_leaf_id': [
                    ('id', 'in', available_cheque_leaf)
                ]
            }
        }
