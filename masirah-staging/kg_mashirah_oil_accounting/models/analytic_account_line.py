from odoo import models, fields, api


class KGAnalyticAccountInherit(models.Model):
    _inherit = "account.analytic.line"

    stock_move_line_id = fields.Many2one('stock.move.line', related="move_line_id.stock_move_line_id")
    material_consumption_line_id = fields.Many2one('material.consumption.line')
