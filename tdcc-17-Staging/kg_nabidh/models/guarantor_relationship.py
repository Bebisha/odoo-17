from odoo import models, fields, api, _



class KgGuarantorRelationship(models.Model):
    _name = 'guarantor.relationship'

    code = fields.Char(string="Code")
    name = fields.Char(string="Description")