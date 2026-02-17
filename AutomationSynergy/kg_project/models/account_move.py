from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    buyer_ord_no = fields.Char()
    buyer_date = fields.Date()
    project_id = fields.Many2one('project.project')
    sale_order_id = fields.Many2one('sale.order', string="Sale Order")
    percent = fields.Float('Percentage',compute="compute_percentage")

    def compute_percentage(self):
        for rec in self:
            rec.percent =False
            if rec.sale_order_id:
                rec.percent = rec.amount_total_signed / rec.sale_order_id.amount_total
