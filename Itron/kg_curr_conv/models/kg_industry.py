# models/hr_designation.py

from odoo import models, fields

class KgIndustry(models.Model):
    _name = 'kg.industry'
    _description = 'Industry'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(required=True)
    company_id = fields.Many2one('res.company', string="Company", required=True, default = lambda self: self.env.company)

