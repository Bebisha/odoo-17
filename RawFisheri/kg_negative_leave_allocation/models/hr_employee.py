from odoo import models, fields


class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    _description = 'hr.employee'

    has_negative_leave = fields.Boolean(string='Has Negative Leave Balance?')
    negative_leave = fields.Char(string='Negative Leave')
