
from odoo import models, fields, api, _



class KgTreatmentRefusal(models.Model):
    _name = 'treatment.refusal'

    code = fields.Char(string="Code")
    name = fields.Char(string="Description")