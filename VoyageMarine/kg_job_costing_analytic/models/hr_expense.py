from odoo import models, fields, api

class HrExpense(models.Model):
    _inherit = 'hr.expense'

    @api.onchange('sale_order_id')
    def _onchange_sale_order(self):
        for rec in self:
            if rec.sale_order_id and rec.sale_order_id.analytic_account_id:
                analytic = rec.sale_order_id.analytic_account_id
                rec.analytic_distribution = {
                    str(analytic.id): 100.0
                }
            else:
                rec.analytic_distribution = {}