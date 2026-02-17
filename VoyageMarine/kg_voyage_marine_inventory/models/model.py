from odoo import models, fields,_

class RecModel(models.Model):
    _name = 'rec.model'
    _description = 'Model Master'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Model Name', required=True)