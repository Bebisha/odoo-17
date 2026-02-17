from odoo import models, fields


class KGDocumentsAccessWIzard(models.TransientModel):
    _name = "document.access.wizard"
    _description = "Documents Access Wizard"

    name = fields.Char(string="Name")
    document_id = fields.Many2one("documents.document", string="Document")

    current_access_users = fields.Many2many("res.users", string="Current Access Users")
    current_access_groups = fields.Many2many("res.groups", 'all_gp_rel',string="Current Access Groups")
    file_access_users = fields.Many2many("res.users", 'file_users_rel', string="File Access users")
    file_groups_access = fields.Many2many("res.groups",'file_gp_rel',string="File Access Groups")

    is_add_users = fields.Boolean(default=False, string="Add Users")
    is_add_groups = fields.Boolean(default=False, string="Add Groups")
    is_remove_users = fields.Boolean(default=False, string="Remove Users")
    is_remove_groups = fields.Boolean(default=False, string="Remove Groups")

    user_ids = fields.Many2many("res.users", "users_doc_rel", string="Users")
    group_ids = fields.Many2many("res.groups", string="Groups")

    remove_user_ids = fields.Many2many("res.users", 'rmv_users_rel', string="Remove Users")
    remove_groups_ids = fields.Many2many("res.groups", 'rmv_groups_rel', string="Remove Groups")

    def update_access_users(self):
        if self.document_id:
            if self.is_add_users:
                self.document_id.file_user_ids |= self.user_ids
            if self.is_add_groups:
                self.document_id.kg_group_ids |= self.group_ids
            if self.is_remove_users:
                self.document_id.file_user_ids -= self.remove_user_ids
            if self.is_remove_groups:
                self.document_id.kg_group_ids -= self.remove_groups_ids
