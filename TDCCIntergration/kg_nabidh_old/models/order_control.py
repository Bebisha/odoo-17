
from odoo import models, fields, api, _



class KgOrderControl(models.Model):
    _name = 'order.control'

    code = fields.Char(string="Value")
    name = fields.Char(string="Description")