from odoo import models, fields, api, _



class KgPriority(models.Model):
    _name = 'priority.form'

    code = fields.Char(string="Code")
    name = fields.Char(string="Description")