# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class VendorEmail(models.TransientModel):
    _name = 'vendor.rfq.mail'
    _description = 'Send Mail for Vendors'

    def _default_requisition_line(self):
        req_id = self.env.context.get('active_id')

        line = self.env['requisition.line'].search([('requisition_id', '=', req_id)])
        return line

    @api.model
    def default_get(self, fields_list):
        res = super(VendorEmail, self).default_get(fields_list)
        req_id = self.env.context.get('active_id')
        # line = self.env['requisition.line'].search([('pr_requisition_id', '=', req_id)])
        line = self.env['requisition.line'].search(
            [('requisition_id', '=', req_id), ('is_rfq_needed', '=', True)])
        req_obj = self.env['material.purchase.requisition'].browse(req_id)
        vals = []
        for rec in line:
            vals.append((0, 0, {
                'requisition_action': 'purchase_order',
                'req_line_id': str(rec.id),
                'product_id': rec.product_id.id,
                'description': rec.description,
                'demand_qty': abs(rec.qty - rec.stock_qty),
                # 'demand_qty': abs(rec.demand_qty - rec.qty_needed_for_mr) - abs((rec.update_picking_qty) - (rec.purchase_quantity)),
                'po_quantity': abs(rec.qty - rec.stock_qty),
                'update_quantity': rec.po_quantity,
                'uom_id': rec.uom_id.id,
                'analytic_account_id': rec.analytic_id.id,
                # 'project_id': rec.project_id.id
            }))
        res.update({'rfq_line_ids': vals,
                    'user_id': req_obj.purchase_user_id.id})
        return res

    vendor_ids = fields.Many2many('res.partner', string='Vendors', required=True)
    user_id = fields.Many2one('res.users', string="Buyer")

    mr_requistion_id = fields.Many2one('material.purchase.requisition', string='MR')
    purchase_requistion_id = fields.Many2one('purchase.requisitions', string='PR')
    requisition_line_ids = fields.Many2many('requisition.line', string="Requisition Line ID",
                                            default=_default_requisition_line)
    rfq_line_ids = fields.Many2many('rfq.lines', string="Requisition Line ID",
                                    )

    @api.onchange('requisition_line_ids')
    def _onchange_requisition_line_ids(self):
        users = self.env.ref('purchase.group_purchase_manager').users.ids
        return {'domain': {'user_id': [('id', 'in', users)]}}

    def create_po(self):
        """ function for create po from wizard view """
        for rec in self:
            context = self._context
            # self.purchase_requistion_id = context.get('active_id')
            # self.mr_requistion_id = context.get('active_id')
            # purchase_requisition = self.purchase_requistion_id
            purchase_requisition = rec.mr_requistion_id
            requisition_lines = rec.rfq_line_ids
            rfq = False
            alternative_rfq_ids = []
            for vendor in rec.vendor_ids:
                rfq = self.create_rfq(vendor, purchase_requisition, requisition_lines, rec.user_id)
                alternative_rfq_ids.append(rfq.id)

            if rfq:
                # remove the existing rfq if from the alternating RFQ list.
                alternative_rfq_ids.remove(rfq.id)
            purchase_requisition.is_check_availablity = True
            self.update_po_qty()
            # purchase_requisition.is_rfq_needed = True
            return {
                'name': 'Purchase Order',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'purchase.order',
                'res_id': rfq.id,
                # 'context': {'default_project_id': self.id}
            }
            # rfq.write({
            #     'alternative_po_ids': [(6, 0, alternative_rfq_ids)],
            # })

    def update_po_qty(self):
        for rec in self:
            for rfq_line in rec.rfq_line_ids:
                requisition_line = rec.requisition_line_ids.filtered(lambda rl: rl.product_id == rfq_line.product_id)
                if requisition_line:
                    requisition_line.po_quantity += rfq_line.po_quantity
                    # requisition_line.update_quantity += rfq_line.po_quantity
        return True

    def create_rfq(self, vendor, purchase_requisition, requisition_lines, user_id):
        """Create Quotation from Purchase Request"""
        purchase_order_obj = self.env['purchase.order'].sudo()
        rfq_lines = []

        existing_draft_pos = purchase_order_obj.search([
            ('state', '!=', 'cancel'),
            # ('order_line.product_qty', '>', 0)
        ])


        for line in requisition_lines:

            if not line.po_quantity:
                raise ValidationError('Quantity for purchasing is not mentioned')
            if line.po_quantity <= 0:
                raise ValidationError('Purchasing quantity has to be a positive number.')
            if line.demand_qty < line.po_quantity:
                raise ValidationError('Purchasing quantity should not be greater than demand quantity!')

            po_line_vals = {
                'product_id': line.product_id.id,
                               # .po_quantity,
                'product_qty': line.demand_qty,
                'name': line.description if line.description else ' ',
                'price_unit': line.product_id.standard_price,

                # 'analytic_distribution': {line.analytic_account_id.id: 100},
                'date_planned': fields.Datetime.now(),
                'product_uom': line.uom_id.id,
                'req_line_id': line.req_line_id,
            }
            rfq_lines.append((0, 0, po_line_vals))

        rfq = purchase_order_obj.sudo().create({
            'partner_id': vendor.id,
            'date_order': fields.Datetime.now(),
            'requisition_po_id': purchase_requisition.id,
            'project_id': purchase_requisition.project_id.id,
            'payment_term_id': vendor.property_supplier_payment_term_id.id,
            # 'pr_requisition_id': purchase_requisition.id,
            # 'pr_requisition_ids': purchase_requisition.ids,
            'origin': purchase_requisition.sequence,
            'state': 'draft',
            'picking_type_id': purchase_requisition.picking_type_id.id,
            'order_line': rfq_lines,
            'user_id': user_id.id,
        })


        return rfq


class RFQLine(models.TransientModel):
    _name = 'rfq.lines'
    _description = 'Send Mail for Vendors'



    rfq_id = fields.Many2one('vendor.rfq.mail')
    requisition_action = fields.Selection([
        ('purchase_order', 'Purchase Order'),
        ('po_and_picking', 'Both PO and Picking'),
        ('internal_picking', 'Internal Picking')],
        string="Requisition Action", default='purchase_order')
    req_line_id = fields.Char('Req Line ID', store=True)
    product_id = fields.Many2one('product.product', string="Product", domain="[('type','not in',['service'])]",
                                 store=True)

    description = fields.Text(string="Description", store=True)
    demand_qty = fields.Float(string="Quantity", default=1.0)
    po_quantity = fields.Float(string="PO Qty", help="Quantity to purchase")
    purchase_quantity = fields.Float(string="Purchased Qty", default=0)
    update_quantity = fields.Float(string="update Qty", )
    uom_id = fields.Many2one('uom.uom', string="Unit Of Measure")
    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account")
    is_error = fields.Boolean(string='bool')

