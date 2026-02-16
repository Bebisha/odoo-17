from odoo import api, fields, models, _
from odoo.http import request


class InvoiceEmail(models.Model):
    _inherit = 'account.move'

    invoice_num = fields.Char(string="Invoice Number")
