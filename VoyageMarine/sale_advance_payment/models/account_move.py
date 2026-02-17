from odoo import fields, models

class KGSaleAdvanceAccountMove(models.Model):
    _inherit = "account.move"

    sale_id = fields.Many2one("sale.order", string="Sale Reference")

