# -*- coding: utf-8 -*-
from odoo import fields, models


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    vessel_id = fields.Many2one('sponsor.sponsor', string="Vessel", related="warehouse_id.vessel_id", store=True)
    is_non_sale_location = fields.Boolean(default=False, string="Is Non-Sale Location",
                                          related="warehouse_id.is_non_sale_location", store=True)
