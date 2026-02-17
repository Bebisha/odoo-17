from odoo import models, fields, api, _



class KgDiagnosisType(models.Model):
    _name = 'diagnosis.type'

    code = fields.Char(string="Value")
    name = fields.Char(string="Description")

