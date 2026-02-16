from odoo import models, fields, api, _



class KgResultStatusCode(models.Model):
    _name = 'result.status.code'

    code = fields.Char(string="Code")
    name = fields.Char(string="Description")