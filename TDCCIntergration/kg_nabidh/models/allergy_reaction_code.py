from odoo import models, fields, api, _



class KgAllergyReactionCode(models.Model):
    _name = 'allergy.reaction.code'

    code = fields.Char(string="Value")
    name = fields.Char(string="Description")