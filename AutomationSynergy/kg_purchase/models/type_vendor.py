from odoo import models, fields

class VendorType(models.Model):
    _name = 'res.vendor.type'
    _description = 'Vendor Type Master'

    name = fields.Char(string='Vendor Type', required=True)
    code = fields.Char(string='Code')  # optional
