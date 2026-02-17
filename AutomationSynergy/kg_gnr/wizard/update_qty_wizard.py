from odoo import fields, models, _
from odoo.exceptions import UserError


class KGUpdateQtyWizard(models.TransientModel):
    _name = "kg.update.qty.wizard"
    _description = "Update Quantity"

    name = fields.Char(string='Name')
    shipment_id = fields.Many2one("shipment.advice", string="Shipment Id")
    line_ids = fields.One2many('kg.update.qty.wizard.line', 'update_qty_wiz_id', string='Line Ids')

    def kg_update_qty_button(self):
        self.shipment_id.is_update_qty = True
        for line in self.line_ids:
            if line.shipping_qty < line.shortage_qty:
                raise UserError(_("Total shortage quantity should not exceed shipping quantity"))

            line.shipment_advice_summary_id.write({
                'scrapped_package_qty': line.shortage_qty,
                'reason': line.reason,
                'received_packaging_qty': line.shipping_qty - line.shortage_qty,
            })
            # for vals in line.shipment_advice_summary_id:
            #     for data in vals.summary_lines:
            #         data.qty_done = vals.received_packaging_qty
            #         data.remaining_qty = vals.received_packaging_qty


class KGUpdateQtyWizardLine(models.TransientModel):
    _name = "kg.update.qty.wizard.line"
    _description = "Update Quantity Line"

    update_qty_wiz_id = fields.Many2one('kg.update.qty.wizard')
    product_id = fields.Many2one('product.product', string='Product')
    shortage_qty = fields.Float(string='Shortage Quantity')
    shipping_qty = fields.Float(string="Shipping Qty")
    shipment_advice_summary_id = fields.Many2one('shipment.advice.summary', string="Shipment Advice Summary Id")
    reason = fields.Char(string="Reason")
