from odoo import models, fields, api, _



class KgRoute(models.Model):
    _name = 'route.form'

    code = fields.Char(string="Value")
    name = fields.Char(string="Description")