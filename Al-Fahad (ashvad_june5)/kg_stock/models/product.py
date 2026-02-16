# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    warehouse_ids = fields.Many2many('stock.warehouse',string='Warehouses')