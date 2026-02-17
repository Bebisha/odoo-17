from odoo import models, fields, api, _



class KgDocumentConfidentialStatus(models.Model):
    _name = 'document.confidential.status'

    code = fields.Char(string="Value")
    name = fields.Char(string="Description")