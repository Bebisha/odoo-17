from odoo import models, fields


class KGVisaDesignation(models.Model):
    _name = "visa.designation"
    _description = "Visa Designation"
    _inherit = ['mail.thread']

    name = fields.Char(string="Name", required=True)