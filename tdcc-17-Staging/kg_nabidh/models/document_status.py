
from odoo import models, fields, api, _



class KgDocumentStatus(models.Model):
    _name = 'document.status'

    code = fields.Char(string="Code")
    name = fields.Char(string="Description")