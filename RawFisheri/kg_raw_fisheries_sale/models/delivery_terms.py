from odoo import models, fields


class KGDeliveryTerms(models.Model):
    _name = "delivery.terms"
    _description = "Delivery Terms"
    _inherit = ['mail.thread']

    name = fields.Char(string="Delivery Terms", required=True)
