# -*- coding: utf-8 -*-
from odoo import fields, models, api, _

class StockValuationLayer(models.Model):
    _inherit = 'stock.valuation.layer'

    vessel_id = fields.Many2one('sponsor.sponsor', string='Vessel', copy=False, compute='compute_vessel_id',store=True)
    kilograms = fields.Float(string='Kilograms', compute='compute_qty_in_kg')
    is_non_sale_location = fields.Boolean(default=False, string="Is Non-Sale Location",
                                          related="warehouse_id.is_non_sale_location", store=True)

    @api.depends('quantity', 'uom_id')
    def compute_qty_in_kg(self):
        for update in self:
            ref_qty = update.uom_id.factor_inv
            update.write({
                'kilograms': update.quantity * ref_qty
            })

    @api.depends('warehouse_id')
    def compute_vessel_id(self):
        """Compute vessel_id in stock valuation."""
        sponsor = self.env['sponsor.sponsor']
        for layer in self:
            layer.vessel_id = sponsor.search([('warehouse_id', '=', layer.warehouse_id.id)],
                                             limit=1).id if layer.warehouse_id else False
