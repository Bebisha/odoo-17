from odoo import models, fields, api


class HRReligion(models.Model):
    _name = "hr.religion"
    _description = "Employee Religion"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Religion")
