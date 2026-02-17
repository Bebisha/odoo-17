from odoo import models, fields,_

class RecMake(models.Model):
    _name = 'rec.make'
    _description = 'Make Master'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Make Name', required=True)