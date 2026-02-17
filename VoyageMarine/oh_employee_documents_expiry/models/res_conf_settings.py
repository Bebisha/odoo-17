from ast import literal_eval

from odoo import models, fields, api

class ResCompany(models.Model):
    _inherit = 'res.company'

    hr_expiry_manager_ids = fields.Many2many('res.users', string='Users for Expiry Notification')

class EmployeeConfiguring(models.TransientModel):
    _inherit = 'res.config.settings'

    hr_expiry_manager_ids = fields.Many2many('res.users',related='company_id.hr_expiry_manager_ids', string='Users for Expiry Notification',readonly=False)

