# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import date


class WizardCreateRFQ(models.TransientModel):
    _name = 'wizard.create.rfq'
    _description = "Create RFQ"

    vendor_id = fields.Many2one(
        'res.partner',
        string="Vendor",
        required=True,
        domain="[('supplier_rank', '>', 0)]"
    )
    item_line_ids = fields.One2many('wizard.item.line', 'line_id', string='Line Item')

    # action to create RFQ
    def action_submit_rfq(self):
        rfq = self.env['purchase.order']
        lines = []
        for item in self.item_line_ids:
            lines.append((0, 0, {
                'product_id': item.product_id.id,
                'product_qty': item.quantity,
                'price_unit': item.price
            }))
        rfq.create({
            'partner_id': self.vendor_id.id,
            'date_order': date.today(),
            'order_line': lines
        })


class WizardItemLine(models.TransientModel):
    _name = 'wizard.item.line'

    line_id = fields.Many2one('wizard.create.rfq', string='Line Item')
    product_id = fields.Many2one('product.product', string="Product", domain="[('detailed_type', '=', 'product')]")
    quantity = fields.Float(string="Quantity")
    price = fields.Float(string="Unit Price")
