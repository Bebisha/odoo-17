# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class VendorEmail(models.TransientModel):
    _name = 'vendor.rfq.mail'
    _description = 'Send Mail for Vendors'

    @api.model
    def default_get(self, fields_list):
        res = super(VendorEmail, self).default_get(fields_list)

        req_id = self.env.context.get('active_id')
        if not req_id:
            return res

        req_obj = self.env['purchase.requisitions'].browse(req_id)
        lines = self.env['requisition.line'].search([
            ('pr_requisition_id', '=', req_id)
        ])

        vals = []
        for rec in lines:
            vals.append((0, 0, {
                'requisition_action': 'purchase_order',
                'req_line_id': rec.id,
                'code': rec.code,
                'product_id': rec.product_id.id,
                'description': rec.description,
                'demand_qty': rec.demand_qty - rec.purchase_quantity,
                'po_quantity': rec.demand_qty,
                'uom_id': rec.uom_id.id,
                'so_id': req_obj.so_id.id,

            }))

        res.update({
            'requisition_line_ids': vals,  # ✅ USE vals here
            'user_id': req_obj.purchase_user_id.id
        })

        return res

    vendor_ids = fields.Many2many('res.partner', string='Vendors', required=True)
    user_id = fields.Many2one('res.users', string="Buyer")
    purchase_requistion_id = fields.Many2one('purchase.requisitions', string='PR')
    requisition_line_ids = fields.Many2many('requisition.line', string="Requisition Line ID")


    # default=_default_requisition_line)

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

    def create_rfq(self, vendor, purchase_requisition, requisition_lines, user_id,code,division_id):
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
                'code': line.code,
                'division_id': division_id,
                'product_id': line.product_id.id,
                'product_qty': line.po_quantity,
                'name': line.description if line.description else ' ',
                'price_unit': line.price_unit,
                'date_planned': fields.Datetime.now(),
                'product_uom': line.uom_id.id,
                'req_line_id': line.req_line_id,
                'sale_id':line.so_id.id,
                'analytic_distribution':{str(line.so_id.analytic_account_id.id): 100.0} if line.so_id.analytic_account_id else {},
                'pr_requisition_id':purchase_requisition.id

            }
            rfq_lines.append((0, 0, po_line_vals))

        # vendor_code = vendor.vendor_code
        # sequence = self.env['ir.sequence'].next_by_code('rfq.seq')
        # sequence_new = self.env['ir.sequence'].next_by_code('rfq.seq.new')
        # else_name = f"{vendor_code}_{sequence_new}"
        # estimation = purchase_requisition.so_id.estimation_id.lead_id.enq_no if purchase_requisition.so_id.estimation_id.lead_id.enq_no else purchase_requisition.so_id.opportunity_id.enq_no
        # if estimation:
        #     name = f"{estimation}_{vendor_code}_{sequence}"
        # else:
        #     name = f"{vendor_code}_{sequence_new}"
        vendor_code = code

        # fallback sequence if no estimation
        sequence_new = self.env['ir.sequence'].next_by_code('rfq.seq.new')

        estimation = purchase_requisition.so_id.estimation_id.lead_id.enq_no if purchase_requisition.so_id.estimation_id.lead_id.enq_no else purchase_requisition.so_id.opportunity_id.enq_no

        if estimation:
            # Search existing RFQs for this supplier and this enquiry
            existing_rfqs = self.env['purchase.order'].search([
                ('partner_id', '=', vendor.id),
                ('name', 'ilike', f"{estimation}_{vendor_code}_")
            ])

            # Determine next increment
            next_number = len(existing_rfqs) + 1
            next_number_str = str(next_number).zfill(2)

            # Build RFQ name
            name = f"{estimation}_{vendor_code}_{next_number_str}"

        else:
            # Search existing RFQs for this supplier and this enquiry
            existing_rfqs = self.env['purchase.order'].search([
                ('partner_id', '=', vendor.id),
                ('name', 'ilike', f"{vendor_code}_")
            ])

            # Determine next increment
            next_number = len(existing_rfqs) + 1
            next_number_str = str(next_number).zfill(2)  # 01, 02, etc.
            # No estimation number, use fallback sequence
            name = f"{vendor_code}_{next_number_str}"

        rfq = purchase_order_obj.sudo().create({
            'name': name,
            'partner_id': vendor.id,
            'date_order': fields.Datetime.now(),
            'pr_requisition_id': purchase_requisition.id,
            'pr_requisition_ids': purchase_requisition.ids,
            'origin': f"{purchase_requisition.sequence or ''}{' - ' if purchase_requisition.lead_id else ''}{purchase_requisition.lead_id.name if purchase_requisition.lead_id else ''}",
            'state': 'draft',
            'picking_type_id': purchase_requisition.picking_type_id.id,
            'order_line': rfq_lines,
            'user_id': user_id.id,
            'so_ids': [(6, 0, purchase_requisition.so_id.ids)],
            'requisition_po_id': purchase_requisition.requisition_id.id,
            'purchase_type_id': purchase_requisition.purchase_type_id.id,
            'purchase_division_id': purchase_requisition.purchase_division_id.id,
            'division_id':division_id

        })

        self.purchase_requistion_id.update({
            'po_ids': [fields.Command.link(rfq.id)],
            'po_date':rfq.date_order,
        })
        self.purchase_requistion_id.requisition_id.update({
            'po_ids': [fields.Command.link(rfq.id)],})

        return rfq

