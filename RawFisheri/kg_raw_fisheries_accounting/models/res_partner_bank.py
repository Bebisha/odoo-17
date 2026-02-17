from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'res.partner.bank'

    iban_no = fields.Char(string="IBAN")
    swift_code = fields.Char(string="Swift Code")
    correspondent_bank = fields.Char(string="Correspondent Bank")
    correspondent_swift_code = fields.Char(string="Correspondent Swift Code")
    correspondent_acc_no = fields.Char(string="Correspondent Account Number")
    is_correspondent_bank = fields.Boolean(default=False, string="Correspondent Bank")
