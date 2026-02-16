# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class VendorEmail(models.TransientModel):
    _name = 'vendor.rfq.mail'
    _description = 'Send Mail for Vendors'

    def _default_requisition_line(self):
        req_id = self.env.context.get('active_id')
        line = self.env['requisition.line'].search([('pr_requisition_id', '=', req_id)])
        return line

    @api.model
    def default_get(self, fields_list):
        res = super(VendorEmail, self).default_get(fields_list)
        req_id = self.env.context.get('active_id')
        line = self.env['requisition.line'].search([('pr_requisition_id', '=', req_id)])
        req_obj = self.env['purchase.requisitions'].browse(req_id)
        vals = []
        for rec in line:
            vals.append((0, 0, {
                'requisition_action': 'purchase_order',
                'req_line_id': str(rec.id),
                'product_id': rec.product_id.id,
                'description': rec.description,
                'demand_qty': rec.demand_qty - rec.purchase_quantity,
                'po_quantity': rec.po_quantity,
                'uom_id': rec.uom_id.id,
            }))
        res.update({'requisition_line_ids': vals,
                    'user_id': req_obj.purchase_user_id.id})
        return res

    vendor_ids = fields.Many2many('res.partner', string='Vendors', required=True)
    user_id = fields.Many2one('res.users', string="Buyer")

    purchase_requistion_id = fields.Many2one('purchase.requisitions', string='PR')
    requisition_line_ids = fields.Many2many('requisition.line', string="Requisition Line ID",
                                            default=_default_requisition_line)

    @api.onchange('requisition_line_ids')
    def _onchange_requisition_line_ids(self):
        users = self.env.ref('purchase.group_purchase_manager').users.ids
        return {'domain': {'user_id': [('id', 'in', users)]}}

    def create_po(self):
        """ function for create po from wizard view """
        for rec in self:
            context = self._context
            self.purchase_requistion_id = context.get('active_id')
            purchase_requisition = self.purchase_requistion_id
            requisition_lines = self.requisition_line_ids
            rfq = False
            alternative_rfq_ids = []
            for vendor in rec.vendor_ids:
                rfq = self.create_rfq(vendor, purchase_requisition, requisition_lines, rec.user_id)
                alternative_rfq_ids.append(rfq.id)
            if rfq:
                # remove the existing rfq if from the alternating RFQ list.
                alternative_rfq_ids.remove(rfq.id)
                # rfq.write({
                #     'alternative_po_ids': [(6, 0, alternative_rfq_ids)],
                # })

    def create_rfq(self, vendor, purchase_requisition, requisition_lines, user_id):
        """Create Quotation from Purchase Request"""
        purchase_order_obj = self.env['purchase.order'].sudo()
        rfq_lines = []
        for line in requisition_lines:
            if not line.po_quantity:
                raise ValidationError('Quantity for purchasing is not mentioned')
            if line.po_quantity <= 0:
                raise ValidationError('Purchasing quantity has to be a positive number.')
            if line.demand_qty < line.po_quantity:
                raise ValidationError('Purchasing quantity should not be greater than demand quantity!')

            po_line_vals = {
                'product_id': line.product_id.id,
                'product_qty': line.po_quantity,
                'name': line.description if line.description else ' ',
                'price_unit': line.price_unit,
                'date_planned': fields.Datetime.now(),
                'product_uom': line.uom_id.id,
                'req_line_id': line.req_line_id,
            }
            rfq_lines.append((0, 0, po_line_vals))
        rfq = purchase_order_obj.sudo().create({
            'partner_id': vendor.id,
            'date_order': fields.Datetime.now(),
            'pr_requisition_id': purchase_requisition.id,
            'pr_requisition_ids': purchase_requisition.ids,
            'origin': purchase_requisition.sequence,
            'state': 'draft',
            'picking_type_id': purchase_requisition.picking_type_id.id,
            'order_line': rfq_lines,
            'user_id': user_id.id,
        })
        return rfq
