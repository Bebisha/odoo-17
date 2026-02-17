from odoo import models, fields

class KGPhysical(models.Model):
    _name="physical.status"
    _description = "Physical status"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Name")