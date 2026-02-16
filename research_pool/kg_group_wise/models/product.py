# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    branch_id = fields.Many2one('kg_branch',)

class ProductProduct(models.Model):
    _inherit = 'product.product'

    branch_id = fields.Many2one('kg_branch')