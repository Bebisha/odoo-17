from odoo import models, fields, api, _



class KgRace(models.Model):
    _name = 'race.form'

    code = fields.Char(string="Code")
    name = fields.Char(string="Description")