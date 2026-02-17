from odoo import api, fields, models


class AccountMove(models.Model):
    """Inherited sale order model"""
    _inherit = "account.move"

    is_subscription = fields.Boolean(string='Is Subscription', default=False,
                                     help='Is subscription')
    subscription_id = fields.Many2one('subscription.package',
                                      string='Subscription',
                                      help='Choose subscription package')

    @api.model_create_multi
    def create(self, vals_list):
        """ It displays subscription in account move """
        for rec in vals_list:
            so_id = self.env['sale.order'].search(
                [('name', '=', rec.get('invoice_origin'))], limit=1)
            if so_id.is_subscription is True:
                new_vals_list = [{'is_subscription': True,
                                  'subscription_id': so_id.subscription_id.id}]
                vals_list[0].update(new_vals_list[0])
        return super().create(vals_list)

class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    def _create_payments(self):
        res = super(AccountPaymentRegister, self)._create_payments()
        for rec in self.line_ids:
            if rec.move_id.payment_state == 'paid':
                if rec.move_id.subscription_id:
                    amc_contract = rec.env['project.contract.request.amc'].search([('subscription_id','=',rec.move_id.subscription_id.id)])
                    contract = rec.env['project.contract.request'].search([('subscription_id','=',rec.move_id.subscription_id.id)])

                    if amc_contract:
                        amc_contract.project_id.write({
                            'is_show':False
                        })
                    elif contract:
                        contract.project_id.write({
                            'is_show': False
                        })

        return res







