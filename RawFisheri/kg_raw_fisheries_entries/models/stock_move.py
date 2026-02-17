from odoo import models, fields


class KGStockMoveInherit(models.Model):
    _inherit = "stock.move"

    stock_date = fields.Date(string='Inventory Date')

    def _prepare_common_svl_vals(self):
        res = super()._prepare_common_svl_vals()
        res['stock_date'] = self.stock_date
        return res

