# -*- coding: utf-8 -*-
from collections import defaultdict

from odoo import fields, models, _, api
from odoo.exceptions import UserError
from ast import literal_eval


class ResPartner(models.Model):
    _inherit = "res.partner"

    success_pack_line_ids = fields.One2many('kg.success.pack.line', 'partner_id', string='Success Pack Lines')
    sale_line_ids = fields.One2many('sale.order', 'kg_partner_id', string='Success Pack Lines')

