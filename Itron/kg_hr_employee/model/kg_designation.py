# models/hr_designation.py

from odoo import models, fields

class HRDesignation(models.Model):
    _name = 'hr.designation'
    _description = 'Designation'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "A Designation with the same name already exists."),
    ]

    name = fields.Char(required=True)
    company_id = fields.Many2one('res.company', string="Company", required=True, default = lambda self: self.env.company)


