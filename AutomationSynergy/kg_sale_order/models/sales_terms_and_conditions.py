from odoo import models, fields, api


class SalesTermsAndCondition(models.Model):
    _name = 'sale.terms.conditions'

    name = fields.Char('Name')
    terms_condition = fields.Html('Terms and Conditions')
