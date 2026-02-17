from odoo import models, api, fields


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    is_supervisor = fields.Boolean(string='Supervisor')
