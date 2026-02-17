from odoo import models, fields, api, _



class KgPatientProfession(models.Model):
    _name = 'patient.profession'

    code = fields.Char(string="Value")
    name = fields.Char(string="Description")