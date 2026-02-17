from odoo import models


class KGStockMoveInherit(models.Model):
    _inherit = "stock.move"

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        res = super()._prepare_move_line_vals(quantity=quantity, reserved_quant=reserved_quant)
        move = self.browse(res['move_id']) if res.get('move_id') else None
        if move and move.sale_line_id.batch_id:
            res['batch_id'] = move.sale_line_id.batch_id.id
        return res

