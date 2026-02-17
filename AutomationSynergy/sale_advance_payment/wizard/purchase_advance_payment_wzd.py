# -*- coding: utf-8 -*-
##############################################################################

import odoo.addons.decimal_precision as dp
from odoo import models, fields, api, exceptions, _


class AccountVoucherPOWizard(models.TransientModel):
    _name = "po.account.voucher.wizard"

    journal_id = fields.Many2one('account.journal', 'Journal', required=True)
    amount_total = fields.Float('Amount total', readonly=True)
    amount_advance = fields.Float('Amount advanced', required=True,
                                  digits=dp.get_precision('Product Price'))
    date = fields.Date("Date", required=True,
                       default=fields.Date.context_today)
    exchange_rate = fields.Float("Exchange rate", digits=(16, 6), default=1.0,
                                 readonly=True)
    currency_id = fields.Many2one("res.currency", "Currency", readonly=True)
    currency_amount = fields.Float("Curr. amount", digits=(16, 2),
                                   readonly=True)
    payment_ref = fields.Char("Ref.")
    cheque_no = fields.Char("Cheque No.")
    cheque_date = fields.Date("Cheque Date")

    @api.constrains('amount_advance')
    def check_amount(self):
        if self.amount_advance <= 0:
            raise exceptions.ValidationError(_("Amount of advance must be "
                                               "positive."))
        if self.env.context.get('active_id', False):
            order = self.env["purchase.order"]. \
                browse(self.env.context['active_id'])
            if self.amount_advance > order.amount_resisual:
                raise exceptions.ValidationError(_("Amount of advance is "
                                                   "greater than residual "
                                                   "amount on purchase"))

    @api.model
    def default_get(self, fields):
        res = super(AccountVoucherPOWizard, self).default_get(fields)
        purchase_ids = self.env.context.get('active_ids', [])
        if not purchase_ids:
            return res
        purchase_id = purchase_ids[0]

        payment_ref = ''
        purchase = self.env['purchase.order'].browse(purchase_id)
        amount_total = purchase.amount_resisual

        if 'amount_total' in fields:
            if purchase.order_line:
                for each in purchase.order_line:
                    payment_ref = payment_ref + str(each.product_id.name) + ','
            res.update({'amount_total': amount_total, 'payment_ref': payment_ref,
                        'currency_id': purchase.currency_id.id})

        return res

    @api.onchange('journal_id', 'date')
    def onchange_date(self):
        if self.currency_id:
            self.exchange_rate = 1.0 / \
                                 (self.env["res.currency"].with_context(date=self.date).
                                  _get_conversion_rate(self.currency_id,
                                                       (self.journal_id.currency_id or
                                                        self.env.user.company_id.
                                                        currency_id), self.env.user.company_id, self.date)
                                  or 1.0)
            self.currency_amount = self.amount_advance * \
                                   (1.0 / self.exchange_rate)
        else:
            self.exchange_rate = 1.0

    @api.onchange('amount_advance')
    def onchange_amount(self):
        self.currency_amount = self.amount_advance * (1.0 / self.exchange_rate)

    def make_advance_payment(self):
        """Create customer paylines and validates the payment"""
        payment_obj = self.env['account.payment']
        purchase_obj = self.env['purchase.order']

        purchase_ids = self.env.context.get('active_ids', [])
        if purchase_ids:
            purchase_id = purchase_ids[0]
            purchase = purchase_obj.browse(purchase_id)

            partner_id = purchase.partner_id.id
            date = self[0].date

            company = purchase.company_id
            context = {'default_approval_state': 'approved'}
            payment_res = {'payment_type': 'outbound',
                           'partner_id': partner_id,
                           'partner_type': 'supplier',
                           'journal_id': self[0].journal_id.id,
                           'company_id': company.id,
                           'currency_id': purchase.currency_id.id,
                           'date': date,
                           'amount': self[0].amount_advance,
                           'purchase_id': purchase.id,
                           'ref': "Advance Payment - " + purchase.name,
                           'payment_ref': self[0].payment_ref,
                           # 'cheque_no': self[0].cheque_no,
                           # 'cheque_date': self[0].cheque_date,
                           # 'communication':
                           #     self[0].payment_ref or purchase.name,
                           'payment_method_id': self.env.
                           ref('account.account_payment_method_manual_in').id
                           }
            payment = payment_obj.with_context(default_approval_state='approve').create(payment_res)
            payment.action_post()
            purchase.advance_paid = True
            details_list = []
            # if purchase.project_rel_id:
            #     details_list.append((0, 0, {'name':'Purchase Advance Payment:'+payment.name , 'amount': self[0].amount_advance,}))
            #     purchase.project_rel_id.mobilization_ids = details_list

        return {
            'type': 'ir.actions.act_window_close',
        }


class purchaseOrder(models.Model):
    _inherit = 'purchase.order'

    advance_paid = fields.Boolean(default=False)
