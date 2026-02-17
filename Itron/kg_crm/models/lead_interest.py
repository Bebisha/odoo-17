from odoo import fields, models


class LeadInterest(models.Model):
    _name = "lead.interest"
    _description = "Lead Interest"

    name = fields.Char('Name',required=True)

class LeadActivityStatus(models.Model):
    _name = "lead.activity.status"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Lead Activity Status"

    name = fields.Char('Name',required=True)
