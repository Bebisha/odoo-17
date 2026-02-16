from odoo import models, fields, api


class KGAccountMoveLineInherit(models.Model):
    _inherit = "account.move.line"

    stock_move_line_id = fields.Many2one('stock.move.line', compute="compute_get_sml")

    def compute_get_sml(self):
        for rec in self:
            if rec.sale_line_ids:
                sml_id = self.env['stock.move.line'].search([('company_id', '=', rec.company_id.id)]).filtered(
                    lambda x: x.sale_line_id.id in rec.sale_line_ids.ids)
                if sml_id:
                    rec.stock_move_line_id = sml_id.id
                else:
                    rec.stock_move_line_id = False
            else:
                rec.stock_move_line_id = False



