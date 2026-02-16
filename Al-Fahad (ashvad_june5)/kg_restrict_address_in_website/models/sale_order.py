# -*- coding: utf-8 -*-
from odoo import fields, models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    ref_no = fields.Char('Reference Number', copy=False, store=True)
