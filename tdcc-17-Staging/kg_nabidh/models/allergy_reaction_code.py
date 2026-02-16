from odoo import models, fields, api, _



class KgAllergyReactionCode(models.Model):
    _name = 'allergy.reaction.code'

    code = fields.Char(string="Code")
    name = fields.Char(string="Description")