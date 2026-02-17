from odoo import models, fields


class KGResPartnerBankInherit(models.Model):
    _inherit = "res.partner.bank"

    bank_iban_number = fields.Char(string="IBAN Number")
    is_default = fields.Boolean(string="Is Default Bank")