# -*- coding: utf-8 -*-

from odoo import models, fields


class KGSponsor(models.Model):
    _name = 'sponsor.sponsor'

    name = fields.Char(string='Name')
    is_vessel = fields.Boolean(string='Vessel')
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
