from odoo import models, fields


class PurchaseEnquiryType(models.Model):
    _name = "purchase.enquiry.type"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Purchase Enquiry Type"

    name = fields.Char(string="Name")