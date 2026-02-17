from odoo import models, fields, api, _



class KgAllergySevertyCode(models.Model):
    _name = 'allergy.severty.code'

    code = fields.Char(string="Value")
    name = fields.Char(string="Description")