from odoo import models, fields, api, _



class KgDiagnosisService(models.Model):
    _name = 'diagnosis.service'

    code = fields.Char(string="Value")
    name = fields.Char(string="Description")