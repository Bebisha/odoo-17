from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    asf_date = fields.Date(string='ASF Date')
    model_no = fields.Char(string='Model No.')




class VendorPurchaseReport(models.Model):
    _name = "vendor.purchase.report"

    vendor = fields.Char(string='Vendor')
    product_id = fields.Many2one('product.product', string='Product')
    model_id = fields.Many2one('product.model', 'Model')
    po_number = fields.Char(string='PO Number')
    vendor_date = fields.Date(string='Vendor Date')
    asf_date = fields.Date(string='ASF Date')
    qty_pending = fields.Integer(string='Qty Pending')

    def vendor_purchase_report(self):
        list_val = []
        for purchase in self.env['purchase.order'].search([('state', '=', 'purchase')]):
            for order_line in purchase.order_line:
                pending_receiver_qty = order_line.product_qty - order_line.qty_received
                model_name = order_line.product_id.model_id.id if order_line.product_id.model_id else None
                if pending_receiver_qty > 0:
                    vals = {
                        'vendor': purchase.partner_id.name,
                        'vendor_date': purchase.date_planned,
                        'model_id': model_name,
                        'po_number': purchase.name,
                        'product_id': order_line.product_id.id,
                        'qty_pending': pending_receiver_qty,
                        'asf_date': purchase.asf_date,
                    }
                    obj_val = self.env['vendor.purchase.report'].create(vals)
                    list_val.append(obj_val.id)

        return {
            'name': 'Vendor Wise Pending Order',
            'view_mode': 'tree',
            'domain': [('id', 'in', list_val)],
            'res_model': 'vendor.purchase.report',
            'type': 'ir.actions.act_window',
            'context': {},
            'target': 'main'
        }
