from odoo import models, fields


class KGDocumentWorkspacesInherit(models.Model):
    _inherit = "documents.folder"

    access_users = fields.Many2many("res.users", string="Access Users")
