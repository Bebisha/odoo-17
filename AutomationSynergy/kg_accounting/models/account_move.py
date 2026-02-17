from odoo import models, fields


class KGAccountMoveInherit(models.Model):
    _inherit = "account.move"

    base_bank_iban_no = fields.Char(string="Base IBAN", compute="compute_base_bank_iban_no")
    inv_bank_iban_no = fields.Char(string="INV IBAN", compute="compute_inv_bank_iban_no")

    def compute_base_bank_iban_no(self):
        for rec in self:
            rec.base_bank_iban_no = False
            if rec.company_id and rec.company_id.bank_ids:
                bank_ids = rec.company_id.bank_ids.filtered(lambda x: x.currency_id.id == rec.company_id.currency_id.id)
                if bank_ids:
                    iban = bank_ids.mapped('iban_no')
                    if iban:
                        rec.base_bank_iban_no = ",".join(iban)

    def compute_inv_bank_iban_no(self):
        for rec in self:
            rec.inv_bank_iban_no = False
            if rec.company_id and rec.company_id.bank_ids:
                bank_ids = rec.company_id.bank_ids.filtered(lambda x: x.currency_id.id == rec.currency_id.id)
                if bank_ids:
                    iban = bank_ids.mapped('iban_no')
                    if iban:
                        rec.inv_bank_iban_no = ",".join(iban)

