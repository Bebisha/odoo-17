from odoo import models, fields

class DeliveryTerms(models.Model):
    _name = 'delivery.terms'
    _description = 'Delivery Terms'
    _inherit = ['mail.thread']

    name = fields.Char(string='Name', required=True)
    description = fields.Html(string='Terms and Conditions', required=True)
