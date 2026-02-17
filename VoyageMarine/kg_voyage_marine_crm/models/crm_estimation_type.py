from odoo import models, fields

class CrmEstimationTypes(models.Model):
    _name = 'crm.estimation.type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "CRM Estimation Type"

    name = fields.Char(string='Type Of Work')