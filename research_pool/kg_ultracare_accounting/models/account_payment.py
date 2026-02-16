from odoo import models, fields, api, _


class KGAccountPayment(models.Model):
    _inherit = 'account.payment'
    _description = 'Account Payment'

    @api.onchange('partner_id')
    def add_cust_vend_rank_domain(self):
        if self.payment_type == 'inbound':
            customer = []
            partner_id = self.env['res.partner'].search([])
            for res in partner_id:
                if res.customer_rank > 0:
                    customer.append(res.id)
            return {
                'domain': {
                    'partner_id': [
                        ('id', 'in', customer)
                    ]
                }
            }
        else:
            supplier = []
            partner_id = self.env['res.partner'].search([])
            for res in partner_id:
                if res.supplier_rank > 0:
                    supplier.append(res.id)
            return {
                'domain': {
                    'partner_id': [
                        ('id', 'in', supplier)
                    ]
                }
            }

    cheque_date = fields.Date(string='Cheque Date')
    cheque_no = fields.Char(string='Cheque Number')


class KGAccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'
    _description = 'Account Payment Register'

    cheque_date = fields.Date(string='Cheque Date')
    cheque_no = fields.Char(string='Cheque Number')
    account_payment_id = fields.Many2one('account.payment', string='Account Payment Id')

    def _create_payment_vals_from_wizard(self, batch_result):
        res = super(KGAccountPaymentRegister, self)._create_payment_vals_from_wizard(batch_result)
        payment_vals = {
            'cheque_date': self.cheque_date,
            'cheque_no': self.cheque_no,
        }
        res.update(payment_vals)
        return res
