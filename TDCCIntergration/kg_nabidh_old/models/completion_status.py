
from odoo import models, fields, api, _



class KgCompletionStatus(models.Model):
    _name = 'completion.status'

    code = fields.Char(string="Value")
    name = fields.Char(string="Description")