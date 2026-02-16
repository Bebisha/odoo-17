

from odoo import fields, models

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Add the custom reference field
    client_order_ref = fields.Char(string='Reference Number')