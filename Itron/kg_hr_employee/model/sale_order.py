# -*- coding: utf-8 -*-

from odoo import models, api, fields
from datetime import datetime


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def link_invoice(self):
        for rec in self:
            if rec.origin:
                inv_list = eval(rec.origin)
                move_obj = self.env['account.move'].search([('name', 'in', inv_list)])
                for m in move_obj:
                    for line in m.invoice_line_ids:
                        # Filter sale order lines based on product_id
                        sale_line_obj = rec.mapped('order_line').filtered(
                            lambda x: x.product_id.id == line.product_id.id)

                        # Update the sale_line_ids in the invoice line
                        for s in sale_line_obj:
                            line.write({'sale_line_ids': [(4, s.id)]})

                        # Update the invoice_lines in the sale order line
                        sale_line_obj.write({'invoice_lines': [(4, line.id)]})
