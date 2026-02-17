# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ProductLocationWiseStock(models.TransientModel):
    _name = "product.loc.stock"
    _description = "Location wise product stock"

    product_id = fields.Many2one("product.product", "Product")
    product_stock_line_ids = fields.One2many("product.loc.stock.line", 'pro_loc_stock_id')

    @api.onchange('product_id')
    def onchange_product(self):
        if self.product_id:
            stock_quant = self.env['stock.quant'].search(
                [('product_id', '=', self.product_id.id), ('quantity', '>', 0),
                 ('location_id.usage', 'in', ['internal', 'transit']),('location_id.is_service_location','!=',True)])
            stock_lines = [(5, 0, 0)]
            for rec in stock_quant:
                stock_lines.append((0, 0, {
                    "location_id": rec.location_id.id,
                    "quantity": sum(rec.mapped('quantity'))}))
                self.write({'product_stock_line_ids': stock_lines})


class ProductLocationWiseStockLine(models.TransientModel):
    _name = "product.loc.stock.line"
    _description = "Location wise product stock Lines"

    location_id = fields.Many2one("stock.location", "Location" )
    pro_loc_stock_id = fields.Many2one("product.loc.stock", "Product stock location")
    quantity = fields.Float("Quantity")
