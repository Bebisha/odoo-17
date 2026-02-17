from odoo import models, fields

class PurchaseTermsConditions(models.Model):
    _name = 'purchase.terms.conditions'
    _description = 'Purchase Terms and Conditions'

    name = fields.Char(string='Name', required=True)
    description = fields.Html(string='Terms and Conditions', required=True)
