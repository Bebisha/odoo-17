from odoo import models, fields


class KGPaymentTermInherit(models.Model):
    _inherit = "account.payment.term"

    days = fields.Integer(string="Days")
