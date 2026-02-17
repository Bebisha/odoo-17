from odoo import models, fields

class SaleOrderConfirmWizard(models.TransientModel):
    _name = 'sale.order.confirm.wizard'
    _description = 'Sale Order Confirm Wizard'

    po_reference = fields.Char('Customer PO Reference', help='Please enter the Customer’s Purchase Order Reference before confirming this quotation.')
    order_id = fields.Many2one('sale.order', string='Quotation', required=True)

    def action_confirm_with_reference(self):
        self.ensure_one()
        self.order_id.purchase_reference = self.po_reference
        return {'type': 'ir.actions.act_window_close'}
