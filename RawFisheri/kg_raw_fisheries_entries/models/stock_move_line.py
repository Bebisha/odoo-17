# -*- coding: utf-8 -*-

from odoo import models, fields


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    stock_date = fields.Date(string='Inventory Date')
    batch_id = fields.Many2one("stock.batch", string="Batch")
    warehouse_id = fields.Many2one("stock.warehouse", related="move_id.warehouse_id")
    is_non_sale_location = fields.Boolean(default=False, string="Is Non-Sale Location",
                                          related="warehouse_id.is_non_sale_location", store=True)
