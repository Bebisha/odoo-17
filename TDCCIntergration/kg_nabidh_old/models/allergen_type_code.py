from odoo import models, fields, api, _



class KgAllergenTypeCode(models.Model):
    _name = 'allergen.type.code'

    code = fields.Char(string="Value")
    name = fields.Char(string="Description")