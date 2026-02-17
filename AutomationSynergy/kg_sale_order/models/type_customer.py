from odoo import models, fields

class CustomerType(models.Model):
    _name = 'res.customer.type'
    _description = 'Customer Type Master'

    name = fields.Char(string='Customer Type', required=True)
    code = fields.Char(string='Code')
