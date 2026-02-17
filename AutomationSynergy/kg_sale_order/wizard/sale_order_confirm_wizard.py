from odoo import models, fields

class SaleOrderConfirmWizard(models.TransientModel):
    _name = 'sale.order.confirm.wizard'
    _description = 'Sale Order Confirm Wizard'

    project_name = fields.Char('Project Name', help='Please enter the Project name before confirming this quotation.')
    order_id = fields.Many2one('sale.order', string='Quotation', required=True)

    def action_confirm_with_prj_name(self):
        self.ensure_one()
        self.order_id.project_name = self.project_name
        # self.order_id
        return {'type': 'ir.actions.act_window_close'}
