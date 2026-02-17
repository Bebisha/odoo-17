from odoo import fields, models


class KGResPartnerInherit(models.Model):
    _inherit = "res.partner"

    pre_payment = fields.Boolean(string="Prepayment", default=False)