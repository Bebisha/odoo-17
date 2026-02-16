
from odoo import models, fields, api, _



class KgOrderControl(models.Model):
    _name = 'order.control'

    code = fields.Char(string="Code")
    name = fields.Char(string="Description")