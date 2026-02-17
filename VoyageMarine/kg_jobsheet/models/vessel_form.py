from odoo import models, fields, api, _



class KgVesselForm(models.Model):
    _name = 'vessel.form'


    code = fields.Char(string="code")
    name = fields.Char(string="Vessel",relate="job_vessel")
    imo_number = fields.Char(string="IMO number")