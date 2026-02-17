# -*- coding: utf-8 -*-

from odoo import fields, models, _, api
from odoo.exceptions import ValidationError


class SaleOrderInherit(models.Model):
    _inherit = "sale.order"

    request_id = fields.Many2one('kg.material.request')


    def action_cancel(self):
        for rec in self:
            done_pickings = rec.picking_ids.filtered(lambda p: p.state == 'done')
            if done_pickings:
                raise ValidationError(_(
                    "You cannot cancel this Sales Order because the delivery has already been validated."
                ))
        return super(SaleOrderInherit, self).action_cancel()

    @api.model
    def create(self, vals):
        sale_order = super(SaleOrderInherit, self).create(vals)
        if not sale_order.kg_lpo:
            sale_order.kg_lpo = sale_order.name
        return sale_order


class SaleOrderLineInherit(models.Model):
    _inherit = "sale.order.line"

    default_code = fields.Char(string="Part code", related='product_id.default_code')

    @api.depends('product_id')
    def _compute_name(self):
        # Call original logic
        super()._compute_name()
        for line in self:
            # if line.product_id:
            line.name = line.product_id.name




