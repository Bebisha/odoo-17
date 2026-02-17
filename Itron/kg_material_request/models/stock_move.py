# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import ValidationError


class StockMove(models.Model):
    _inherit = "stock.move"

    is_verified = fields.Boolean(string="Is Verified", copy=False)
    qty_status = fields.Selection([
        ('nothing', 'Quantity not entered'),
        ('partial', 'Quantity less than required'),
        ('equal', 'Quantity matches demand'),
        ('greater', 'Quantity exceeds demand')
    ], string="Qty Status", compute="compute_qty_status")
    qty = fields.Float('Request Qty')

    default_code = fields.Char(string="Part code", related='product_id.default_code')

    @api.onchange('qty')
    def compute_qty_status(self):
        for line in self:
            if line.qty == line.product_uom_qty:
                line.qty_status = 'equal'
            elif line.qty == 0:
                line.qty_status = 'nothing'
            elif line.product_uom_qty < line.qty:
                line.qty_status = 'greater'
            else:
                line.qty_status = 'partial'

    def action_verified(self):
        for line in self:
            if not line.qty:
                raise ValidationError(_("Enter quantity before verifying"))
            line.quantity = line.qty
            line.is_verified = True
        if all(line.is_verified for line in self.picking_id.move_ids_without_package):
            self.picking_id.is_verified = True

    def action_reset(self):
        for line in self:
            line.is_verified = False
        self.picking_id.is_verified = False


