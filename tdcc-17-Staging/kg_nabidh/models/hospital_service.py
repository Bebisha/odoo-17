from odoo import models, fields, api, _



class KgHospitalService(models.Model):
    _name = 'hospital.service'

    code = fields.Char(string="Code")
    name = fields.Char(string="Description")