from odoo import models, fields, api, _



class KgState(models.Model):
    _name = 'state.form'

    code = fields.Char(string="Code")
    name = fields.Char(string="Description")