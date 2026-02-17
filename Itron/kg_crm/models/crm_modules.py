from datetime import datetime
from odoo import fields, models, api

class CRMModules(models.Model):
    _name = 'crm.modules'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name')
    product_id = fields.Many2one('product.product', string="Product")