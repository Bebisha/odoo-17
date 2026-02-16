# -*- coding: utf-8 -*-
from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError


class KGStockQuant(models.Model):
    _name = 'kg.stock.quant'
    _description = 'Stock Quants'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char()
    investment_id = fields.Many2one('kg.investment.entry',string='Investment Entry',required=True)
    quantity = fields.Float(
        'Quantity',)
    cost_price = fields.Float(string='Total Cost Price',digits=(10,6))
    last_cost_price = fields.Float(string='Stock Valuation',digits=(10,6))
    avg_cost = fields.Float(string='Average Cost',digits=(10,6))
    price = fields.Float(string='Cost Price',digits=(10,6))
    is_purchase = fields.Boolean(string='Is Purchase', default=False)
    is_sale = fields.Boolean(string='Is Sale', default=False)
    selling_price = fields.Float(string="Selling Price")
