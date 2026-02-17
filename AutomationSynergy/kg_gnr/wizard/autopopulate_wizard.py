# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date, datetime
from odoo import api, fields, models
from odoo.tools import float_repr


class CategoryAutopopulateOrderline(models.TransientModel):
    """Category Autopopulate Orderline wizard."""

    _name = 'po.autopopulate.order.wizard'
    _description = 'PO Autopopulate Orderline'

    @api.model
    def get_default_po_id(self):
        po_line_ids = self.env['purchase.order.line'].search([('order_id.state','=','purchase'),('order_id.purchase_type','!=','local_purchase')])
        po = []
        for po_line in po_line_ids:
            line = self.env['shipment.advice.line'].search([('purchase_line_id', '=', po_line.id)])
            shp_qty = sum(line.mapped('shipped_packaging_qty'))
            if po_line.product_qty > shp_qty:
                po.append(po_line.order_id.id)
        # # if po_line_id:
        # #     list = []
        # #     for i in po_line_id:
        # #         list.append(i.order_id.id)
        return po

    po_ids = fields.Many2many('purchase.order')
    not_git_po = fields.Many2many('purchase.order', 'kg_not_it_po_rel', string="Not Git PO", default=get_default_po_id)
    auto_line_ids = fields.One2many('po.autopopulate.orderline.wizard', 'wizard_id')

    def action_confirm(self):
        for line in self.auto_line_ids:
            open_packaging_qty = 0.0
            received_qty_packaged = 0.0
            open_qty = line.po_line.product_uom_qty - line.po_line.shipment_adv_qty
            open_packaging_qty = open_qty
            shipment_id = self.env['shipment.advice'].browse(self._context.get('active_ids', [])).id
            order_line_obj = self.env['shipment.advice.line'].create({
                'shipment_id': shipment_id,
                'vendor_id': line.vendor_id.id,
                'product_id': line.product_id.id,
                'purchase_id': line.po_id.id,
                'purchase_line_id': line.po_line.id,
                'open_packaging_qty': open_packaging_qty,
                'shipped_packaging_qty': open_packaging_qty,
                'received_packaging_qty': received_qty_packaged,
                'price': line.price,
                'amount': line.amount,
            })

    @api.onchange('po_ids')
    def po_onchange(self):
        purchase_orders = self.env['purchase.order'].browse(self.po_ids.ids)
        pr_list = []
        append_list = []
        self.auto_line_ids = False
        for order in purchase_orders:
            for line in order.order_line:
                open_qty = line.product_uom_qty - line.shipment_adv_qty
                if open_qty > 0 :
                    append_list.append((0, 0, {
                        'product_id': line.product_id.id,
                        'po_id': order.id,
                        'po_line': line.id,
                        'vendor_id': order.partner_id.id,
                        'remaining_qty': open_qty,
                        'price': line.price_unit,
                        'amount': line.price_subtotal
                    }))
        self.auto_line_ids = append_list


class CategoryAutopopulateOrderlineWiz(models.TransientModel):
    """Category Autopopulate Orderline wizard."""

    _name = 'po.autopopulate.orderline.wizard'
    _description = 'PO Autopopulate Orderline'

    wizard_id = fields.Many2one('po.autopopulate.order.wizard')
    po_id = fields.Many2one('purchase.order')
    po_line = fields.Many2one('purchase.order.line')
    vendor_id = fields.Many2one('res.partner')
    product_id = fields.Many2one('product.product')
    remaining_qty = fields.Float()
    price = fields.Float(string='Price')
    amount = fields.Float(string='Amount')
