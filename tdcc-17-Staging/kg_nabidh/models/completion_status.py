
from odoo import models, fields, api, _



class KgCompletionStatus(models.Model):
    _name = 'completion.status'

    code = fields.Char(string="Code")
    name = fields.Char(string="Description")