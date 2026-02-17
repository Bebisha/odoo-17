
from odoo import models, fields, api, _



class KgOrderType(models.Model):
    _name = 'order.type'

    code = fields.Char(string="Value")
    name = fields.Char(string="Description")