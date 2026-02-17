# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    kilograms = fields.Float(string='Kilograms', compute='compute_qty_in_kg')
    vessel_id = fields.Many2one('sponsor.sponsor', string="Vessel", related="location_dest_id.vessel_id", store=True)

    @api.depends('quantity', 'product_uom_id')
    def compute_qty_in_kg(self):
        for update in self:
            ref_qty = update.product_uom_id.factor_inv

            update.write({
                'kilograms': update.quantity * ref_qty
            })

    @api.model
    def create(self, vals):
        res = super(StockMoveLine, self).create(vals)
        if res and not res.stock_date:
            res.stock_date = fields.Date.today()
        return res
