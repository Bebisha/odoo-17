from odoo import models, fields, api, _



class KgAbnormalFlag(models.Model):
    _name = 'abnormal.flag'

    code = fields.Char(string="Code")
    name = fields.Char(string="Description")