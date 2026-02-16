from odoo import models, fields, api, _



class KgAllergenCodeMnemonicDescription(models.Model):
    _name = 'allergen.code'

    code = fields.Char(string="Code")
    name = fields.Char(string="Description")