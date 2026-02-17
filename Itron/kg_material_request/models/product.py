# -*- coding: utf-8 -*-
from collections import defaultdict
from xml import etree

from odoo import fields, models, _, api
from odoo.exceptions import UserError
from ast import literal_eval

class ProductTemplate(models.Model):
    _inherit = "product.template"
    _rec_name = 'display_name'

    company_id = fields.Many2one(
        'res.company', 'Company', index=True , default=lambda self: self.env.company, readonly=True)

    @api.depends('name', 'default_code')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.name
            if rec.default_code:
                rec.display_name = f"{rec.default_code} - {rec.name}"

class ProductProduct(models.Model):
    _inherit = "product.product"
    _rec_name = 'display_name'

    # context_from_material_request = fields.Boolean(default=False,string="Context")

    @api.depends('name', 'default_code')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.name
            if rec.default_code:
                rec.display_name = f"{rec.default_code} - {rec.name}"

    # is_material_request_user = fields.Boolean(store=True )



