# -*- encoding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class CreatePurchaseWizard(models.TransientModel):
    _name = 'create.purchase.wizard'
    _description = 'Create Purchase Wizard'

    vendor_id = fields.Many2one('res.partner', string='Vendor', readonly=True)
    order_type = fields.Selection([
        ('rfq', 'Request for Quotation'),
        ('po', 'Purchase Order'),
    ], string='Order Type', default='po', required=True)

    line_ids = fields.One2many('create.purchase.line', 'wizards_id', string='Products')
    sale_order_id = fields.Many2one('sale.order', string='Sale Order')

    create_po_button = fields.Boolean(string='Create Purchase Order', compute='_compute_create_po_button')

    create_rfq_button = fields.Boolean(string='Create RFQ', compute='_compute_create_rfq_button')

    @api.depends('order_type')
    def _compute_create_po_button(self):
        for wizard in self:
            wizard.create_po_button = (wizard.order_type == 'po')


    @api.depends('order_type')
    def _compute_create_rfq_button(self):
        for wizard in self:
            wizard.create_rfq_button = wizard.order_type == 'rfq'

    def create_purchase_order(self):
        if not self.sale_order_id:
            raise UserError('Please select a sale order.')

        purchase_order_values = {
            'partner_id':self.sale_order_id.partner_id.id,
            # 'sale_order_id':self.sale_order_id,
            # Add other relevant values from the wizard
        }
        purchase_order = self.env['purchase.order'].create(purchase_order_values)

        for line in self.sale_order_id.order_line:
            purchase_order_line_values = {
                'order_id': purchase_order.id,
                'product_id': line.product_id.id,
                'product_qty': line.product_uom_qty,
                'price_unit': line.price_unit,
                # Add other relevant values from the sale order lines
            }
            self.env['purchase.order.line'].create(purchase_order_line_values)

        # Set the state of the purchase order to 'purchase' and confirm it
        purchase_order.write({'state': 'purchase'})
        purchase_order.button_confirm()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Order',
            'res_model': 'purchase.order',
            'res_id': purchase_order.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.onchange('sale_order_id')
    def _onchange_sale_order_id(self):
        if self.sale_order_id:
            self.vendor_id = self.sale_order_id.partner_id.id
            self.line_ids = [(0, 0, {'product_id': line.product_id.id}) for line in self.sale_order_id.order_line]




    def create_purchase_rfq(self):
        if self.order_type != 'rfq':
            raise UserError('RFQ creation is only available for RFQ order type.')

        rfq_values = {
            'partner_id': self.sale_order_id.partner_id.id,
            # 'sale_order_id': self.sale_order_id,
            # Add other relevant values from the wizard
        }
        rfq = self.env['purchase.order'].create(rfq_values)

        for line in self.line_ids:
            rfq_line_values = {
                'order_id': rfq.id,
                'product_id': line.product_id.id,
                'product_qty': line.product_qty,
                'price_unit': line.price_unit,
                # Add other relevant values from the wizard lines
            }
            self.env['purchase.order.line'].create(rfq_line_values)

        return {
            'type': 'ir.actions.act_window',
            'name': 'RFQ',
            'res_model': 'purchase.order',
            'res_id': rfq.id,
            'view_mode': 'form',
            'target': 'current',
        }


class CreatePurchaseLine(models.TransientModel):
    _name = 'create.purchase.line'
    _description = 'Purchase Order Line'

    wizards_id = fields.Many2one('create.purchase.wizard', string='Wizard')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    product_qty = fields.Float(string='Quantity', default=1.0)
    price_unit = fields.Float(string='Unit Price', default=0.0)