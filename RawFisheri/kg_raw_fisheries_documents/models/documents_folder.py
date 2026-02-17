from odoo import models, fields


class KGDocumentsFolderInherit(models.Model):
    _inherit = "documents.folder"

    folder_group_ids = fields.Many2one("res.groups", string="Folder Access")
    is_notification = fields.Boolean(default=False, string="Notification")
