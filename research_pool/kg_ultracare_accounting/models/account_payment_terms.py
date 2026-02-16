from odoo import fields, models


class KGAccounPaymentTermInherit(models.Model):
    _inherit = "account.payment.term"

    cash_customer = fields.Boolean(string="Cash Customer", default=False)
