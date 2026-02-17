from odoo import models, fields, api, _



class KgAddressType(models.Model):
    _name = 'address.type'

    code = fields.Char(string="Value")
    name = fields.Char(string="Description")