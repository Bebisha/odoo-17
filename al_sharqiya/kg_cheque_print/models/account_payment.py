from odoo import models, fields, api

from odoo.exceptions import ValidationError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    cheque_series = fields.Many2one('cheque.leaf', string="Cheque Book", domain=[('state', '=', 'confirm')])
    journal_type = fields.Boolean(string="Journal Type")
    cheque_leaf_no = fields.Many2one('cheque.leaf.line', string="Cheque No.", tracking=True)
    cheque_payee_name = fields.Char('Payee Name')
    vendor_name_id = fields.Many2one('res.partner', string="Vendor Name")
    cheque_transaction_date = fields.Date(string="Cheque Date")
    pdc_cdc = fields.Selection([('pdc', 'PDC'), ('cdc', 'CDC')], string="Check Type")

    @api.onchange('cheque_series')
    def _onchange_cheque_series(self):
        available_cheque_leaf = []
        if self.cheque_series:
            available_cheque_leaf = self.cheque_series.cheque_leaf_line_ids.filtered(lambda x: x.status == 'draft').ids

        # Find the first available cheque leaf ID
        first_cheque_leaf_id = available_cheque_leaf[0] if available_cheque_leaf else False

        return {
            'domain': {
                'cheque_leaf_no': [
                    ('id', 'in', available_cheque_leaf)
                ]
            },
            'value': {
                'cheque_leaf_no': first_cheque_leaf_id
            }
        }



    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id.display_name:
            self.cheque_payee_name = self.partner_id.name

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        for rec in self:
            if rec.journal_id:
                if rec.journal_id.type == 'bank':
                    self.journal_type = 1

    def action_post(self):
        res = super(AccountPayment, self).action_post()

        for payment in self:
            if payment.cheque_leaf_no:
                # Check if the selected cheque leaf has already been issued
                if any(leaf.status == 'issued' for leaf in payment.cheque_leaf_no):
                    raise ValidationError('This cheque leaf number has already been used in a posted payment.')

                # Mark the cheque leaf as issued and link it to the payment
                payment.cheque_leaf_no.status = 'issued'
                payment.cheque_leaf_no.account_payment_id = payment.id

        return res

    def action_cancel(self):
        res = super(AccountPayment, self).action_cancel()
        if self.cheque_leaf_no:
            self.cheque_leaf_no.status = 'cancel'
        return res

    def update_cheque_leaf_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Update Cheque',
            'res_model': 'update.payment.cheque',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_account_payment_id': self.id,
                'default_current_cheque_leaf_id': self.cheque_leaf_no.id
            }
        }



