
from odoo import models, fields, api, _



class KgOrderStatus(models.Model):
    _name = 'order.status'

    code = fields.Char(string="Value")
    name = fields.Char(string="Description")