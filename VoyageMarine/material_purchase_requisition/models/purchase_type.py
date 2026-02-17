from odoo import models, fields

class PurchaseType(models.Model):
    _name = 'purchase.type'
    _description = 'Purchase Type'

    name = fields.Char(string='Name', required=True)
    purchase_division = fields.Char(string='Purchase Division', required=True)
    purchase_division_id = fields.Many2one('purchase.division', string='Purchase Division', required=True)
    code = fields.Char(string='Code', required=True)

class PurchaseDivision(models.Model):
    _name = 'purchase.division'
    _description = 'Purchase Division'

    name = fields.Char(string='Name', required=True)
    purchase_type_id = fields.Many2one('purchase.type', string='Purchase Type', required=True)
    code = fields.Char(string='Code', required=True)