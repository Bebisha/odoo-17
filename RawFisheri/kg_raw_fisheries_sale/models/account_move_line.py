# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    weight = fields.Float(string='Tons', compute='_compute_total_weight', copy=False, digits=(16, 3))

    @api.depends('quantity', 'discount', 'price_unit', 'tax_ids', 'currency_id')
    def _compute_totals(self):
        for line in self:
            if line.display_type != 'product':
                line.price_total = line.price_subtotal = False
            # Compute 'price_subtotal'.
            line_discount_price_unit = line.price_unit * (1 - (line.discount / 100.0))
            if line.sale_line_ids:
                subtotal = line.weight * line_discount_price_unit
            else:
                subtotal = line.quantity * line_discount_price_unit

            # Compute 'price_total'.
            if line.tax_ids:
                taxes_res = line.tax_ids.compute_all(
                    line_discount_price_unit,
                    quantity=line.weight if line.sale_line_ids else line.quantity,
                    currency=line.currency_id,
                    product=line.product_id,
                    partner=line.partner_id,
                    is_refund=line.is_refund,
                )
                line.price_subtotal = taxes_res['total_excluded']
                line.price_total = taxes_res['total_included']
            else:
                line.price_total = line.price_subtotal = subtotal

    @api.depends('quantity', 'product_uom_id')
    def _compute_total_weight(self):
        """ To compute weights in metric tons """
        for line in self:
            weight = (line.quantity * line.product_uom_id.factor_inv) / 1000
            line.weight = weight


class AccountMove(models.Model):
    _inherit = 'account.move'

    vessel_id = fields.Many2one('sponsor.sponsor', string='Vessel', compute='compute_inventory_details')
    delivery_term = fields.Char(string='Delivery Terms')
    country_origin = fields.Many2one('res.country', string='Country of Origin', compute='compute_inventory_details')
    country_supply = fields.Many2one('res.country', string='Country of Supply', compute='compute_inventory_details')
    place_loading = fields.Many2one('res.country', string='Place of Loading')

    place_of_loading = fields.Char(string='Place of Loading', compute='compute_inventory_details')
    delivery_terms_id = fields.Many2one("delivery.terms", string="Delivery Terms", compute='compute_inventory_details')
    batch_info = fields.Char(string="Batch Info", copy=False)

    def compute_inventory_details(self):
        """ Compute the details from sale order """
        for order in self:
            source_orders = order.line_ids.sale_line_ids.order_id
            order.write({
                'vessel_id': source_orders.vessel_id.id if source_orders else False,
                'delivery_terms_id': source_orders.delivery_terms_id.id if source_orders else False,
                'country_origin': source_orders.country_origin if source_orders else False,
                'country_supply': source_orders.country_supply if source_orders else False,
                'place_of_loading': source_orders.place_of_loading if source_orders else False,
            })
