from odoo import models, fields, api


class CustomTermsAndCondition(models.Model):
    _name = 'custom.terms.conditions'

    name = fields.Char('Name')
    terms_condition = fields.Html('Terms and Conditions')
