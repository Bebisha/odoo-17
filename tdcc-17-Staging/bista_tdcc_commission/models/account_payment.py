# -*- encoding: utf-8 -*-
#
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
#

from odoo import api, fields, models
from datetime import date


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    # @api.multi
    def action_validate_receipt_commission_payment(self):
        self.ensure_one()
        self.post()
        self.receipt_commission_id.update({'state': 'paid'})
        commission_line_ids = self.env['sale.commission.line'].search(
            [('receipt_commission_id', '=', self.receipt_commission_id.id)])
        commission_line_ids.write({'state': 'paid'})
        return True

    @api.model
    def default_get(self, fields):
        rec = super(AccountPayment, self).default_get(fields)
#         if self._context.get('active_model', False) == 'account.invoice':
#             active_id = self._context.get('active_id')
#             invoice = self.env['account.invoice'].browse(active_id)
#             rec.update({
#                 'user_id': invoice.user_id.id or False,
#             })
        if self._context.get('default_receipt_commission_id'):
            receipt_commission_id = self.env['receipt.commission'].browse(
                self._context.get('default_receipt_commission_id'))
            rec.update({
                'amount': receipt_commission_id.amount,
                'payment_type': 'outbound',
                'partner_type': 'supplier',
                'partner_id': receipt_commission_id.partner_id.id,
            })
        return rec

    user_id = fields.Many2one('res.users', string='Salesperson',
                              default=lambda self: self.env.user)
    receipt_commission_id = fields.Many2one('receipt.commission',
                                            string='Receipt Commission Ref.')

    def post_commission_line(self, invoice_id, user_id, payment_amount):
        commission_obj = self.env['sale.commission'].sudo()
        commission_line_vals = {
            'source': self.name,
            'currency_id': self.currency_id.id,
            'invoice_id': invoice_id.id
        }

        commission_id = commission_obj.search_and_create(
            invoice_id.date_invoice, user_id)
        commission_percentage = user_id.commission_percentage
        sales_limit = user_id.sales_limit
        receipt_commission = 0.00
        payment_date = self.payment_date
        if self.payment_method_id.id == self.env.ref(
                'bista_account_pdc.account_payment_method_pdc_in').id:
            payment_date = self.cheque_date
        if commission_percentage:
            tax_amount = (payment_amount * invoice_id.amount_tax) / \
                invoice_id.amount_total
            untaxed_amount = payment_amount - tax_amount
            if not commission_id.commission_line_ids:
                if untaxed_amount > sales_limit:
                    receipt_commission = (
                        (untaxed_amount - sales_limit) *
                        commission_percentage) / 100
            else:
                if commission_id.commission_line_ids.filtered(
                        lambda l: l.commission_amount):
                    receipt_commission = (
                        untaxed_amount * commission_percentage) / 100
                else:
                    total_amount = sum(
                        commission_id.commission_line_ids.mapped(
                            'untaxed_payment_amount')) + untaxed_amount
                    if total_amount > sales_limit:
                        receipt_commission = (
                            (total_amount - sales_limit) *
                            commission_percentage) / 100
            commission_line_vals.update({
                'commission_date': str(payment_date) if not self._context.get(
                    'advance_payment') else date.today(),
                'partner_id': user_id.partner_id.id,
                'commission_amount': receipt_commission,
                'payment_amount': payment_amount,
                'taxed_payment_amount': tax_amount or 0.00,
                'untaxed_payment_amount': untaxed_amount or 0.00,
                'user_type': 'sale_person' or '',
                'state': 'draft'
            })
            if receipt_commission == 0:
                commission_line_vals.update({'state': 'paid'})
            commission_id.commission_line_ids = [
                (0, 0, commission_line_vals)]
            commission_id._compute_amount()
        return True

    # @api.multi
    def post(self):
        res = super(AccountPayment, self).post()
        for rec in self:
            if rec.payment_type == 'inbound':
                if self._context.get('active_model') == 'account.move' and \
                        self._context.get('active_id', False):
                    invoice_id = self.env[self._context.get(
                        'active_model')].browse(self._context.get('active_id'))
                    rec.post_commission_line(invoice_id, rec.user_id,
                                             rec.amount)
        return res
