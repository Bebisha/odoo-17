from odoo import models, fields, api, _



class KgGender(models.Model):
    _name = 'gender.form'

    code = fields.Char(string="Value")
    name = fields.Char(string="Description")