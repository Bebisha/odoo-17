from odoo import fields, models, api


class ResCompany(models.Model):
    _inherit = "res.company"

    aed_iban = fields.Char(
        string="For AED : IBAN No. ")
    usd_iban = fields.Char(
        string="For USD : IBAN No. ")
    bank_swift_code = fields.Char(
        string="BANK SWIFT CODE: ")
    bank_name = fields.Char(
        string="BANK NAME ")

    bank_street = fields.Char(string='Street')
    bank_city = fields.Char(string='City')
    bank_states = fields.Many2one('res.country.state', string='State')
    bank_country = fields.Many2one('res.country', string='Country')
    bank_zip = fields.Integer("ZIP")
    bank_phone_number = fields.Char(string='Phone Number')
    bank_complete_address = fields.Char(string='Address', compute='_compute_complete_address')

    seal = fields.Binary(string="Digital Seal")

    @api.depends('bank_street', 'bank_city', 'bank_states', 'bank_country')
    def _compute_complete_address(self):
        for record in self:
            street = record.bank_street or ''
            city = record.bank_city or ''
            state = record.bank_states.name or ''
            zip = record.bank_zip or ''
            country = record.bank_country.code or ''

            record.bank_complete_address = f"{street},{city},{state},{zip},{country}"
