from odoo import models, fields, api


class KGStockMoveLine(models.Model):
    _inherit = "stock.move.line"

    analytic_account_id = fields.One2many("account.analytic.line", 'stock_move_line_id', string="Analytic Account")
    sale_line_id = fields.Many2one("sale.order.line", compute="compute_soline_id")

    @api.depends('move_id')
    def compute_soline_id(self):
        for rec in self:
            if rec.move_id:
                rec.sale_line_id = rec.move_id.sale_line_id.id
            else:
                rec.sale_line_id = False


