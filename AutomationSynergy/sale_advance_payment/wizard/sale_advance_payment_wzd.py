# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea Servicios Tecnológicos All Rights Reserved
#    $Omar Castiñeira Saaevdra <omar@comunitea.com>$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


import odoo.addons.decimal_precision as dp
from odoo import models, fields, api, exceptions, _


class AccountVoucherWizard(models.TransientModel):
    _name = "account.voucher.wizard"

    journal_id = fields.Many2one('account.journal', 'Journal', required=True)
    amount_total = fields.Float('Amount total', readonly=True)
    advance_percentage = fields.Float('Advance Percentage', default=10.0, required=True)
    amount_advance = fields.Float('Amount advanced', compute='_compute_amount_advance', store=True,
                                  digits=dp.get_precision('Product Price'))
    date = fields.Date("Date", required=True, default=fields.Date.context_today)
    exchange_rate = fields.Float("Exchange rate", digits=(16, 6), default=1.0, readonly=True)
    currency_id = fields.Many2one("res.currency", "Currency", readonly=True)
    currency_amount = fields.Float("Curr. amount", digits=(16, 2), readonly=True)
    payment_ref = fields.Char("Ref.")

    @api.depends('amount_total', 'advance_percentage')
    def _compute_amount_advance(self):
        for wizard in self:
            wizard.amount_advance = (wizard.amount_total * wizard.advance_percentage) / 100.0


    @api.constrains('amount_advance')
    def check_amount(self):
        if self.amount_advance <= 0:
            raise exceptions.ValidationError(_("Amount of advance must be "
                                               "positive."))
        if self.env.context.get('active_id', False):
            order = self.env["sale.order"]. \
                browse(self.env.context['active_id'])
            if self.amount_advance > order.amount_resisual:
                raise exceptions.ValidationError(_("Amount of advance is "
                                                   "greater than residual "
                                                   "amount on sale"))

    @api.model
    def default_get(self, fields):
        res = super(AccountVoucherWizard, self).default_get(fields)
        sale_ids = self.env.context.get('active_ids', [])
        if not sale_ids:
            return res
        sale_id = sale_ids[0]

        payment_ref = ''
        sale = self.env['sale.order'].browse(sale_id)
        amount_total = sale.amount_resisual

        if 'amount_total' in fields:
            if sale.order_line:
                for each in sale.order_line:
                    payment_ref = payment_ref + str(each.product_id.name) + ','
            res.update({'amount_total': amount_total,'payment_ref': payment_ref,
                        'currency_id': sale.pricelist_id.currency_id.id})

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
        sale_obj = self.env['sale.order']

        sale_ids = self.env.context.get('active_ids', [])
        if sale_ids:
            sale_id = sale_ids[0]
            sale = sale_obj.browse(sale_id)

            partner_id = sale.partner_id.id
            date = self[0].date

            company = sale.company_id

            payment_res = {'payment_type': 'inbound',
                           'partner_id': partner_id,
                           'partner_type': 'customer',
                           'journal_id': self[0].journal_id.id,
                           'company_id': company.id,
                           'currency_id':
                               sale.pricelist_id.currency_id.id,
                           'date': date,
                           'amount': self[0].amount_advance,
                           'sale_id': sale.id,
                           'ref': "Advance Payment - " + sale.name,
                           'payment_ref': self[0].payment_ref,
                           # 'communication':
                           #     self[0].payment_ref or sale.name,
                           'payment_method_id': self.env.
                               ref('account.account_payment_method_manual_in').id
                           }
            payment = payment_obj.with_context(default_approval_state='approve').create(payment_res)
            payment_obj.default_invoice()
            # payment.action_post()

            sale.advance_paid = True
            today = date.today()
            # invoice_vals = {
            #     'ref': sale.name,
            #     'move_type': 'out_invoice',
            #     'currency_id': sale.currency_id.id,
            #     'partner_id': sale.partner_id.id,
            #     'user_id': sale.user_id.id,
            #     'invoice_user_id': sale.user_id.id,
            #     'invoice_origin': sale.name,
            #     'company_id': sale.company_id.id,
            #     'invoice_date': today,
            # }
            # invoice_line_ids = []
            # invoice_line_ids.append((0, 0, {
            #     'quantity': 1,
            #     'price_unit':self[0].amount_advance,
            #     'name': 'Advance Payment',
            #     'tax_ids': [(6, 0, [])],
            # })),
            # invoice_vals['invoice_line_ids'] = invoice_line_ids
            # inv_moves = self.env['account.move'].create(invoice_vals)
            # inv_moves.action_post()
            # sale.update({'invoice_ids': [(4, inv_moves.id)]})
            # line_id = inv_moves.invoice_line_ids[0].id
            # for line in sale.order_line:
            #     line.update({'invoice_lines':[(4, line_id)]})
            details_list = []
            # for project in sale.project_ids:
            #     details_list.append((0, 0, {'name':'Sale Advance Payment:'+payment.name , 'amount': self[0].amount_advance,}))
            #     project.mobilization_ids = details_list





        return {
            'type': 'ir.actions.act_window_close',
        }


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    advance_paid = fields.Boolean(default=False)

