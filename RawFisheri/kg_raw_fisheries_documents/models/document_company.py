from odoo import models, fields


class DocumentCompany(models.Model):
    _name = "document.company"
    _description = "Document Company"

    name = fields.Char(string="Name", required=True)