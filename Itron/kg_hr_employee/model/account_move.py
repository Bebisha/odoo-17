# -*- coding: utf-8 -*-

from odoo import models, api, fields
from datetime import datetime


class AccountMove(models.Model):
    _inherit = 'account.move'

    kg_purchase_order_id = fields.Many2one('purchase.order', string="KG Purchase Order")

    def link_so_invoice(self):
        for rec in self:
            if rec.kg_sale_order_id:
                for line in rec.invoice_line_ids:
                    # Filter sale order lines based on product_id
                    sale_line_obj = rec.kg_sale_order_id.mapped('order_line').filtered(
                        lambda x: x.product_id.id == line.product_id.id)

                    # Update the sale_line_ids in the invoice line
                    line.sale_line_ids = [(6, 0, sale_line_obj.ids)]

                    # Update the invoice_lines in the sale order line
                    sale_line_obj.write({'invoice_lines': [(6, 0, line.ids)]})

    def link_payment_with_bills(self):
        for rec in self:
            if rec.ref and rec.payment_state != 'paid':
                payment_ids = self.env['account.payment'].search([('ref', '=', rec.ref), ('state', '=', 'posted'), ('payment_type', '=', 'outbound'), ('partner_type', '=', 'supplier')])
                if payment_ids:
                    lines = (payment_ids.mapped('line_ids') + rec.mapped('line_ids')) \
                        .filtered(lambda line: line.account_id.account_type in ['liability_payable'] and not line.reconciled)
                    lines.reconcile()

    def link_payment_with_invoice(self):
        for rec in self:
            if rec.payment_reference and rec.payment_state != 'paid':
                payment_ids = self.env['account.payment'].search([('ref', '=', rec.payment_reference), ('state', '=', 'posted'), ('payment_type', '=', 'inbound'), ('partner_type', '=', 'customer')])
                if payment_ids:
                    lines = (payment_ids.mapped('line_ids') + rec.mapped('line_ids')) \
                        .filtered(lambda line: line.account_id.account_type in ['asset_receivable'] and not line.reconciled)
                    lines.reconcile()



class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def update_qty_invoiced(self):
        for rec in self:
            for line in rec.order_line:
                line._compute_qty_invoiced()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
