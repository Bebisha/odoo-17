from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    company_code = fields.Char(string='Company Code', required=True)