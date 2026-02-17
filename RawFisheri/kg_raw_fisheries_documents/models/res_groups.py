from odoo import models, fields


class ResGroupsDocumentsInh(models.Model):
    _inherit = "res.groups"

    is_documents_groups = fields.Boolean(default=False,string="Is Documents Group")
