from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    invoice_history_ids = fields.One2many('account.move', 'sale_order_id', ondelete="cascade")
