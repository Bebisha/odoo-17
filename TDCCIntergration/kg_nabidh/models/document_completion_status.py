
from odoo import models, fields, api, _
class KgDocumentCompletionStatus(models.Model):
    _name = 'document.completion.status'

    code = fields.Char(string="Value")
    name = fields.Char(string="Description")