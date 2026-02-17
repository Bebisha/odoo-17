from odoo import models, fields


class SupplierCategory(models.Model):
    _name = "supplier.category"
    _description = "Supplier Category"
    _inherit = ['mail.thread']

    name = fields.Char(string="Supplier Category", required=True)
