from odoo import models, fields


class DocumentDepartment(models.Model):
    _name = "document.department"
    _description = "Document Department"

    name = fields.Char(string="Name", required=True)
