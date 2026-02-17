from odoo import models, fields


class KGStockValuationLayerInherit(models.Model):
    _inherit = "stock.valuation.layer"

    stock_date = fields.Date(string='Inventory Date')