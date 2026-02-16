from odoo import models, fields, api, _



class KgDischargeDisposition(models.Model):
    _name = 'discharge.disposition'

    code = fields.Char(string="Code")
    name = fields.Char(string="Description")