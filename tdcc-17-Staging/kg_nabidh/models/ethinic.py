from odoo import models, fields, api, _



class KgEthinic(models.Model):
    _name = 'ethinic.form'

    code = fields.Char(string="Code")
    name = fields.Char(string="Description")