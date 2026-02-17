from odoo import models, fields

class SaleTermsConditions(models.Model):
    _name = 'sale.terms.conditions'
    _description = 'Sale Terms and Conditions'

    name = fields.Char(string='Name', required=True)
    description = fields.Html(string='Terms and Conditions', required=True)
