from odoo import models, fields, api, _



class KgGuarantorRelationship(models.Model):
    _name = 'guarantor.relationship'

    code = fields.Char(string="Value")
    name = fields.Char(string="Description")