# -*- coding: utf-8 -*-
from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    destination_id = fields.Many2one('stock.location',
        string="Destination Location", related="company_id.destination_id", readonly=False)

    source_id = fields.Many2one('stock.location',
                                     string="Source Location", related="company_id.source_id", readonly=False)

    picking_type_id = fields.Many2one(
        'stock.picking.type',
        string="Picking Type",
        domain="[('code', '=', 'outgoing')]",
        related="company_id.picking_type_id", readonly=False
    )


class ResCompany(models.Model):
    _inherit = "res.company"

    destination_id = fields.Many2one('stock.location',string="Destination Location")
    source_id = fields.Many2one('stock.location',string="Source Location")
    picking_type_id = fields.Many2one(
        'stock.picking.type',
        string="Picking Type",
        domain="[('code', '=', 'outgoing')]"
    )


