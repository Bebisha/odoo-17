from odoo import models, fields, api, _



class KgResultCode(models.Model):
    _name = 'result.code'

    code = fields.Char(string="Value")
    name = fields.Char(string="Description")