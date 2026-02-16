from odoo import models, fields


class ResPartnerBankInherit(models.Model):
    _inherit = "res.partner.bank"

    currency_id = fields.Many2one(tracking=True, default=lambda self: self.env.company.currency_id.id)


class ResPartner(models.Model):
    _inherit = "res.partner"

    vendor_code = fields.Char('Vendor Code')

    def create(self, vals):
        """To create vendor code sequence"""
        rec = super(ResPartner, self).create(vals)
        if rec.supplier_rank >= 1 and rec.name:
            first_letter = rec.name[0].upper()
            sequence_name = f"vendor.code.sequence.{first_letter}"
            sequence = self.env['ir.sequence'].search([('code', '=', sequence_name), ], limit=1)
            if not sequence:
                sequence_vals = {
                    'name': f"Vendor Code Sequence {first_letter}",
                    'code': sequence_name,
                    'padding': 3,
                    'prefix': first_letter,
                }
                sequence = self.env['ir.sequence'].create(sequence_vals)
            rec.vendor_code = sequence.next_by_id() or '/'
        return rec
