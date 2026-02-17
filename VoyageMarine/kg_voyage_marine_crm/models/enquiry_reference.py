from odoo.exceptions import ValidationError, UserError

from odoo import models, fields, api, _


class KGEnquiryReference(models.Model):
    _name = "enquiry.reference"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "EnquiryReference"


    code = fields.Char(string="code")
    name = fields.Char(string="EnquiryReference")


