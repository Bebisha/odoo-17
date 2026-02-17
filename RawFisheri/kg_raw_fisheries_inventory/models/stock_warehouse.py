# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    vessel_id = fields.Many2one('sponsor.sponsor', string='Vessel')
    is_non_sale_location = fields.Boolean(default=False,string="Is Non-Sale Location")

