
from odoo import models, fields, api, _



class KgDocumentAvailablestatus(models.Model):
    _name = 'document.available.status'

    code = fields.Char(string="Code")
    name = fields.Char(string="Description")