from odoo import models, fields, api, _



class KgPatientClass(models.Model):
    _name = 'patient.class'

    code = fields.Char(string="Code")
    name = fields.Char(string="Description")