from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class SalefromPurchase(models.TransientModel):
    _name = "sale.po.creation"
    _description = "PO from SO"

    @api.model
    def get_default_sale_orders(self):
        return self.env['sale.order'].browse(self._context.get('active_ids', [])).ids

    so_ids = fields.Many2many('sale.order', default=get_default_sale_orders)
    vendor_id = fields.Many2one(
        'res.partner', required=True,
        domain=[('supplier_rank', '>', 0), ('is_approved', '=', True)]
    )
    line_ids = fields.One2many('sale.po.creation.line', 'so_po_id')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, string='Company')
    vessel_id = fields.Many2one('vessel.code', string='Vessel')

    def create_draft_po(self):
        sale_orders = self.env['sale.order'].browse(self.so_ids.ids)
        for order in sale_orders:
            if order.po_created:
                raise ValidationError(_(
                    "Purchase order already created from the sale order %(sale_order)s.",
                    sale_order=order.name,
                ))

        vals = self._prepare_po_vals()
        po = self.env['purchase.order'].sudo().create(vals)

        for so in sale_orders:
            so.po_created = True

        return {
            'name': _('PO'),
            'view_mode': 'form',
            'res_model': 'purchase.order',
            'view_id': self.sudo().env.ref('purchase.purchase_order_form').id,
            'type': 'ir.actions.act_window',
            'res_id': po.id,
        }

    def _prepare_po_vals(self):
        sale_orders = self.env['sale.order'].browse(self.so_ids.ids)
        origin = ','.join(sale_orders.mapped('name'))
        po_lines = []

        for rec in self.line_ids:
            po_lines.append((0, 0, {
                'product_id': rec.product_id.id,
                'name': rec.product_id.name,
                'product_qty': rec.quantity,
                'price_unit': rec.purchase_rate,
                'sale_id': rec.sale_order_id.id,
            }))

        if not po_lines:
            raise ValidationError(_("No product list found for purchase order creation"))


        po_vals = {
            'partner_id': self.vendor_id.id,
            'order_line': po_lines,
            'origin': origin,
            'vessel_id': self.vessel_id.id,
            # 'opportunity_id':self.sale_orders.estimation_id.lead_id.enq_no if self.sale_orders.estimation_id else ""
            # 'sale_id': self.vessel_id.id,
        }

        return po_vals

    @api.onchange('so_ids')
    def so_onchange(self):
        sale_orders = self.env['sale.order'].browse(self.so_ids.ids)
        self.line_ids = [(5, 0, 0)]  # Clear existing lines

        product_data = {}

        for order in sale_orders:
            for line in order.order_line:
                product = line.product_id
                key = (product.id, order.id)
                if key not in product_data:
                    product_data[key] = {
                        'quantity': 0.0,
                        'purchase_rate': product.product_tmpl_id.standard_price,
                        'product_id': product.id,
                        'sale_order_id': order.id,
                    }
                product_data[key]['quantity'] += line.product_uom_qty

        new_lines = []
        for val in product_data.values():
            new_lines.append((0, 0, {
                'product_id': val['product_id'],
                'quantity': val['quantity'],
                'purchase_rate': val['purchase_rate'],
                'sale_order_id': val['sale_order_id'],
            }))

        self.line_ids = new_lines


class SaleFromPurchaseLine(models.TransientModel):
    _name = "sale.po.creation.line"

    so_po_id = fields.Many2one('sale.po.creation', string="PO Creation Wizard")
    sale_order_id = fields.Many2one('sale.order', string="Sale Order")  # Track source SO
    product_id = fields.Many2one('product.product', string="Product")
    quantity = fields.Float(string="Quantity")
    purchase_rate = fields.Float(string="Purchase Rate")
