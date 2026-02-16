from odoo import models, fields, api, _



class KgConfidentialityCode(models.Model):
    _name = 'confidentiality.code'

    code = fields.Char(string="Code")
    name = fields.Char(string="Description")