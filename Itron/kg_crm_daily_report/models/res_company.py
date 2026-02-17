from odoo import models,fields,api


class ResCompanyInherit(models.Model):
    _inherit = 'res.company'

    daily_report_manager_ids = fields.Many2many('res.users', string="Daily Report Managers")
