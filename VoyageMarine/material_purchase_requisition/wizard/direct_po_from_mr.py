from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class KGPRPurchase(models.TransientModel):
    _name = "pr.po.creation"
    _description = "PO from PR"

    @api.model
    def get_default_pr(self):
        return self.env['purchase.requisitions'].browse(self._context.get('active_ids', [])).ids

    pr_ids = fields.Many2many('purchase.requisitions', default=get_default_pr)
    vendor_id = fields.Many2one(
        'res.partner', required=True,
        domain=[('supplier_rank', '>', 0), ('is_approved', '=', True)]
    )
    line_ids = fields.One2many('pr.po.creation.line', 'pr_po_id')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, string='Company')
    vessel_id = fields.Many2one('vessel.code', string='Vessel')

    def create_draft_po(self):
        sale_orders = self.pr_ids
        for order in sale_orders:
            if order.po_created:
                raise ValidationError(_(
                    "Purchase order already created from the PR %(sale_order)s.",
                    sale_order=order.sequence,
                ))

        vals = self._prepare_po_vals()
        po = self.env['purchase.order'].sudo().create(vals)

        # Mark PRs as PO created
        sale_orders.write({'po_created': True})

        # Link the PO to all selected PRs
        for pr in sale_orders:
            if pr.requisition_line_ids:
                pr.write({
                    'po_ids': [fields.Command.link(po.id)],
                    'po_date': po.date_order,
                })


                if pr.requisition_id:
                    pr.requisition_id.write({
                        'po_ids': [fields.Command.link(po.id)],
                    })

        return {
            'name': _('PO'),
            'view_mode': 'form',
            'res_model': 'purchase.order',
            'view_id': self.sudo().env.ref('purchase.purchase_order_form').id,
            'type': 'ir.actions.act_window',
            'res_id': po.id,
        }

    def _prepare_po_vals(self):
        sale_orders = self.pr_ids
        po_lines = []

        for rec in self.line_ids:
            pr = rec.pr_id
            so = pr.so_id if pr else False
            po_lines.append((0, 0, {
                'product_id': rec.product_id.id,
                'name': rec.product_id.name if rec.product_id.id else '',
                'product_qty': rec.quantity,
                'price_unit': rec.purchase_rate,
                'req_line_id': pr.id if pr else False,
                'sale_id': so.id if so else False,
                'analytic_distribution': {str(so.analytic_account_id.id): 100.0} if so.analytic_account_id else {},
                'pr_requisition_id': pr.id if pr else False,
            }))

        if not po_lines:
            raise ValidationError(_("No product list found for purchase order creation"))

        # Generate origin from multiple PRs
        origin = ', '.join(sale_orders.mapped('sequence'))
        vendor_code = self.vendor_id.vendor_code

        # Estimation logic
        estimation = ''
        for so in sale_orders.mapped('so_id'):
            if so.estimation_id and so.estimation_id.lead_id and so.estimation_id.lead_id.enq_no:
                estimation = so.estimation_id.lead_id.enq_no
                break
            elif so.opportunity_id and so.opportunity_id.enq_no:
                estimation = so.opportunity_id.enq_no
                break

        if estimation:
            existing_rfqs = self.env['purchase.order'].search([
                ('partner_id', '=', self.vendor_id.id),
                ('name', 'ilike', f"{estimation}_{vendor_code}_")
            ])
            next_number = len(existing_rfqs) + 1
            next_number_str = str(next_number).zfill(2)
            name = f"{estimation}_{vendor_code}_{next_number_str}"
        else:
            existing_rfqs = self.env['purchase.order'].search([
                ('partner_id', '=', self.vendor_id.id),
                ('name', 'ilike', f"{vendor_code}_")
            ])
            next_number = len(existing_rfqs) + 1
            next_number_str = str(next_number).zfill(2)
            name = f"{vendor_code}_{next_number_str}"

        picking_type_id = sale_orders[0].picking_type_id.id if sale_orders else False
        requisition_id = sale_orders[0].requisition_id.id if sale_orders else False
        purchase_type_id = sale_orders[0].purchase_type_id.id if sale_orders else False
        so_ids = sale_orders.mapped('so_id').ids

        po_vals = {
            'name': name,
            'partner_id': self.vendor_id.id,
            'date_order': fields.Datetime.now(),
            'pr_requisition_id': sale_orders[0].id if sale_orders else False,
            'pr_requisition_ids': sale_orders.ids,
            'origin': origin,
            'state': 'draft',
            'picking_type_id': picking_type_id,
            'order_line': po_lines,
            'so_ids': [(6, 0, so_ids)],
            'requisition_po_id': requisition_id,
            'purchase_type_id': purchase_type_id,
            'vessel_id': self.vessel_id.id,
        }

        return po_vals

    @api.onchange('pr_ids')
    def so_onchange(self):
        sale_orders = self.env['purchase.requisitions'].browse(self.pr_ids.ids)
        self.line_ids = [(5, 0, 0)]  # Clear existing lines

        product_data = {}

        for order in sale_orders:
            for line in order.requisition_line_ids:
                product = line.product_id
                key = (product.id, order.id)
                if key not in product_data:

                    product_data[key] = {
                        'quantity': 0.0,
                        'purchase_rate': product.product_tmpl_id.standard_price,
                        'product_id': product.id,
                        # 'sale_order_id': order.id,
                    }
                product_data[key]['quantity'] += line.demand_qty

        new_lines = []

        for val in product_data.values():
            new_lines.append((0, 0, {
                'product_id': val['product_id'],
                'quantity': val['quantity'],
                'purchase_rate': val['purchase_rate'],
                # 'sale_order_id': val['sale_order_id'],
            }))

        self.line_ids = new_lines


class PRFromPurchaseLine(models.TransientModel):
    _name = "pr.po.creation.line"

    pr_po_id = fields.Many2one('pr.po.creation', string="PO Creation Wizard")
    pr_id = fields.Many2one('purchase.requisitions', string="Purchase Requisitions")  # Track source SO
    product_id = fields.Many2one('product.product', string="Product")
    quantity = fields.Float(string="Quantity")
    purchase_rate = fields.Float(string="Purchase Rate")
    uom_id = fields.Many2one('uom.uom', string="Unit Of Measure")
