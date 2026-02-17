# -*- coding: utf-8 -*-
from odoo import fields, models
class ProductProduct(models.Model):
    _inherit = "res.partner"

    is_inv_customer = fields.Boolean("Is Inventory Customer")

