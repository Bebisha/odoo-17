from odoo import models, fields



class PatientAssignedLocation(models.Model):
    _name = 'patient.assigned.location'

    code = fields.Char(string="Value")
    name = fields.Char(string="Description")