from odoo import fields, models


class KGResPartnerBankInherit(models.Model):
    _inherit = 'res.partner.bank'

    iban_no = fields.Char(string="IBAN")
    swift_code = fields.Char(string="Swift Code")