from odoo import models, fields, api, _



class KgUnits(models.Model):
    _name = 'units.code'

    code = fields.Char(string="Code")
    name = fields.Char(string="Description")
    unit = fields.Char(string="Units")
    value = fields.Char(string="Value")