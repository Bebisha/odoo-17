from odoo import models, fields, api, _



class KgGender(models.Model):
    _name = 'gender.form'

    code = fields.Char(string="Code")
    name = fields.Char(string="Description")