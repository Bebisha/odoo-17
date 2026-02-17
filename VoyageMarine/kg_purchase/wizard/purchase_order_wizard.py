# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import time
from odoo import api, fields, models, _
from datetime import datetime

from odoo.exceptions import UserError, ValidationError


class createpurchaseorder(models.TransientModel):
    _name = 'create.purchaseorder'
    _description = "Create Purchase Order"

    sale_id = fields.Many2many('sale.order', string='Sale Order Id')
    new_order_line_ids = fields.One2many('getsale.orderdata', 'new_order_line_id', string="Order Line")
    partner_id = fields.Many2one('res.partner', string='Vendor', required=True,
                                 domain=[('supplier_rank', '>', 0), ('is_approved', '=', True)])
    date_order = fields.Datetime(string='Order Date', required=True, copy=False, default=fields.Datetime.now)
    vessel_id = fields.Many2one('vessel.code', string='Vessel')

    from odoo.osv import expression

    @api.model
    def default_get(self, default_fields):
        res = super(createpurchaseorder, self).default_get(default_fields)
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))

        sale_order_ids = [(6, 0, sale_orders.ids)]
        res.update({'sale_id': sale_order_ids})

        update = []
        for record in sale_orders.mapped('order_line'):
            if record.product_uom_qty - record.po_qty and record.product_id.detailed_type == 'product':
                update.append((0, 0, {
                    'product_id': record.product_id.id,
                    'product_uom': record.product_uom.id,
                    'order_id': record.order_id.id,
                    'order_line_id': record.id,
                    'name': record.name,
                    'product_qty': record.product_uom_qty - record.po_qty,
                    'price_unit': record.price_unit,
                    'product_subtotal': record.price_subtotal,

                }))

        res.update({'new_order_line_ids': update})

        if not update:
            raise UserError("Already RFQ Created")

        return res

    def action_create_purchase_order(self):
        self.ensure_one()
        res = self.env['purchase.order'].browse(self._context.get('id', []))
        value = []
        so = self.env['sale.order'].browse(self._context.get('active_id'))
        pricelist = self.partner_id.property_product_pricelist

        partner_pricelist = self.partner_id.property_product_pricelist
        sale_order_name = so.name
        vessel_id = so.vessel_id.id
        company_id = self.env.company

        if self.partner_id.property_purchase_currency_id:
            currency_id = self.partner_id.property_purchase_currency_id.id
        else:
            currency_id = self.env.company.currency_id.id

        purchase_order = res.create({
            'partner_id': self.partner_id.id,
            'date_order': str(self.date_order),
            'origin': sale_order_name,
            'vessel_id':vessel_id,
            'partner_ref': sale_order_name,
            'currency_id': currency_id,
            'estimation_id': self.sale_id.estimation_id.id,
            'project_ids': self.sale_id.project_ids.ids,
            'so_ids': [(6, 0, self.sale_id.ids)]

        })
        self.sale_id.est_so_ids |= purchase_order

        sale_order = self.env['sale.order'].browse(self._context.get('active_ids', []))
        message = "Purchase Order created " + '@' + purchase_order.name
        sale_order.message_post(body=message)

        for data in self.new_order_line_ids:
            if data.order_line_id.balance_qty < data.product_qty:
                raise UserError('Entered Qty should not be greater than Balance Qty')

            sale_order_name = data.order_id.name or so.name
            product_quantity = data.product_qty
            purchase_qty_uom = data.product_uom._compute_quantity(product_quantity, data.product_id.uom_po_id)

            supplierinfo = data.product_id._select_seller(
                partner_id=purchase_order.partner_id,
                quantity=purchase_qty_uom,
                date=purchase_order.date_order and purchase_order.date_order.date(),
                uom_id=data.product_id.uom_po_id
            )
            fpos = purchase_order.fiscal_position_id
            taxes = fpos.map_tax(data.product_id.supplier_taxes_id)
            if taxes:
                taxes = taxes.filtered(lambda t: t.company_id.id == company_id.id)

            if not supplierinfo:
                po_line_uom = data.product_uom or data.product_id.uom_po_id
                price_unit = self.env['account.tax']._fix_tax_included_price_company(
                    data.product_id.uom_id._compute_price(data.product_id.standard_price, po_line_uom),
                    data.product_id.supplier_taxes_id,
                    taxes,
                    company_id,
                )
                if price_unit and data.order_id.currency_id and data.order_id.company_id.currency_id != data.order_id.currency_id:
                    price_unit = data.order_id.company_id.currency_id._convert(
                        price_unit,
                        data.order_id.currency_id,
                        data.order_id.company_id,
                        self.date_order or fields.Date.today(),
                    )
            else:
                price_unit = self.env['account.tax'].sudo()._fix_tax_included_price_company(
                    supplierinfo.price,
                    data.product_id.supplier_taxes_id,
                    taxes,
                    company_id
                )
                if purchase_order.currency_id and supplierinfo.currency_id != purchase_order.currency_id:
                    price_unit = supplierinfo.currency_id._convert(
                        price_unit, purchase_order.currency_id, purchase_order.company_id, fields.datetime.today()
                    )

            line_values = {
                'product_id': data.product_id.id,
                'product_code': data.product_id.default_code,
                'name': data.name,
                'product_qty': data.product_qty,
                'order_id': purchase_order.id,
                'product_uom': data.product_uom.id,
                'taxes_id': data.product_id.supplier_taxes_id.ids,
                'date_planned': data.date_planned,
                'sale_id': self.sale_id.id
            }

            if not self.partner_id.property_purchase_currency_id:
                line_values['price_unit'] = price_unit

            self.env['purchase.order.line'].create(line_values)
            data.order_line_id.po_qty += data.product_qty

        # Redirect to the created purchase order's form view
        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Order',
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'res_id': purchase_order.id,
            'target': 'current',
        }


class Getsaleorderdata(models.TransientModel):
    _name = 'getsale.orderdata'
    _description = "Get Sale Order Data"

    new_order_line_id = fields.Many2one('create.purchaseorder')

    product_id = fields.Many2one('product.product', string="Product", required=True)
    name = fields.Char(string="Description")
    product_qty = fields.Float(string='Quantity', required=True)
    date_planned = fields.Datetime(string='Scheduled Date', default=datetime.today())
    product_uom = fields.Many2one('uom.uom', string='Product Unit of Measure')
    order_id = fields.Many2one('sale.order', string='Order Reference', ondelete='cascade', index=True)
    order_line_id = fields.Many2one('sale.order.line', string='Order Line Reference', ondelete='cascade', index=True)
    price_unit = fields.Float(string='Unit Price', digits='Product Price')
    product_subtotal = fields.Float(string="Sub Total", compute='_compute_total')

    @api.depends('product_qty', 'price_unit')
    def _compute_total(self):
        for record in self:
            record.product_subtotal = record.product_qty * record.price_unit
