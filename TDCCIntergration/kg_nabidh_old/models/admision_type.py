from odoo import models, fields, api, _



class KgAdmissionType(models.Model):
    _name = 'admision.type'

    code = fields.Char(string="Value")
    name = fields.Char(string="Description")