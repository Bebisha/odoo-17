# -*- coding: utf-8 -*-

from odoo import models, fields, _, api, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_round, float_is_zero, groupby
from datetime import date


class SubShipmentAdvice(models.Model):
    _name = 'sub.shipment.advice'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Sub Shipment Advice'
    _rec_name = 'name'
    _order = 'name desc, id desc'

    name = fields.Char(string='RReferencer', required=True, readonly=True, default=lambda self: _('New'), copy=False)
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', 'Responsible', copy=False, default=lambda self: self.env.user, required=True,
                              tracking=True)
    state = fields.Selection(
        string='Status',
        selection=[
            ('draft', 'Draft'),
            ('done', 'Confirmed'),
            ('closed', "Closed"),
        ],
        required=True, tracking=True, default='draft')
    date = fields.Date('Date', tracking=True,default=fields.Date.today)
    notes = fields.Text('Notes')
    shipment_lines = fields.One2many(comodel_name='sub.shipment.advice.line', inverse_name='shipment_id',
                                     string='Shipment Products', required=False, tracking=True)
    git_id = fields.Many2one('shipment.advice',readonly=True,store=True,string='Shipment Advice')



    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('sub.shipment.advice') or 'New'
        result = super(SubShipmentAdvice, self).create(vals)
        return result

    def action_confirm(self):
        self.state = 'done'


class ShipmentAdviceLinesub(models.Model):
    _name = 'sub.shipment.advice.line'
    _description = 'Shipment Advice Line'
    _rec_name = 'product_id'

    vendor_id = fields.Many2one('res.partner')
    shipment_id = fields.Many2one(
        'sub.shipment.advice', 'Shipment', ondelete='cascade', required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    purchase_id = fields.Many2one('purchase.order', 'Purchase', ondelete='cascade', required=True, copy=False,
                                  domain="[('state', 'in', ('purchase', 'done'))]")
    purchase_line_id = fields.Many2one(
        'purchase.order.line', 'Product Description', required=True,
        domain="[('order_id', '=', purchase_id), ('order_id', '=', purchase_id), ('product_id', '=', product_id)]")
    company_id = fields.Many2one(related='shipment_id.company_id')
    product_packaging_id = fields.Many2one(related='purchase_line_id.product_packaging_id')
    open_packaging_qty = fields.Float(string='Open Qty', readonly=1)
    shipped_packaging_qty = fields.Float(string='Shipped Qty', digits='Product Unit of Measure')
    received_qty = fields.Float(string='Rec. Qty(Unit)', digits='Product Unit of Measure',
                                related='purchase_line_id.qty_received')
    received_packaging_qty = fields.Float(string='Received Qty', digits='Product Unit of Measure')


    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            po_lines = self.env['purchase.order.line'].search(
                [('order_id.state', 'in', ('purchase', 'done')),
                 ('product_id', '=', self.product_id.id)])
            po_line_ids = po_lines.filtered(lambda l: (l.product_uom_qty - l.shipment_adv_qty) > 0)
            return {
                'domain': {
                    'purchase_id': [('id', 'in', po_line_ids.mapped('order_id').ids)]
                }
            }

    @api.onchange('purchase_line_id')
    def _onchange_purchase_line_id(self):
        open_packaging_qty = 0.0
        received_qty_packaged = 0.0
        if self.purchase_line_id:
            self.vendor_id = self.purchase_line_id.order_id.partner_id.id
            open_qty = self.purchase_line_id.product_uom_qty - self.purchase_line_id.shipment_adv_qty
            open_packaging_qty = open_qty
        self.update({
            'open_packaging_qty': open_packaging_qty,
            'shipped_packaging_qty': open_packaging_qty,
            'received_packaging_qty': received_qty_packaged,
        })

    @api.onchange('shipped_packaging_qty')
    def _onchange_shipped_packaging_qty(self):
        result = {}
        if self.shipped_packaging_qty > self.open_packaging_qty:
            result['warning'] = {
                'title': _('Warning'),
                'message': _('Shipped quantity should not be exceed open qty.'),
            }
        return result


