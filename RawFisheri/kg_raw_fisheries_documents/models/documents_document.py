import time
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class KGDocumentsDocumentInherit(models.Model):
    _inherit = "documents.document"

    tag_id = fields.Many2one("documents.tag", string="Tag")
    view_user_ids = fields.Many2many("res.users", 'view_users_rel', string="View Users", compute="compute_view_users",
                                     store=True)
    file_user_ids = fields.Many2many("res.users", 'file_access_rel', string="File Users")
    document_type_id = fields.Many2one("document.type", string="Type")
    document_date = fields.Date(string="Date")
    validity_start_date = fields.Date(string="Start Date")
    validity_end_date = fields.Date(string="End Date")
    document_department_ids = fields.Many2many("document.department", string="Departments")
    document_department_id = fields.Many2one("document.department", string="Department")
    document_company_id = fields.Many2one("document.company", string="Company")
    country_ids = fields.Many2many("res.country", string="Allowed Countries")
    country_id = fields.Many2one("res.country", string="Country")
    counter_party_id = fields.Many2one("res.partner", string="Counterparty", domain=[('supplier_rank', '>', 0)])
    original_file_name = fields.Char(string="Original File")
    upload_date = fields.Date(string="Upload Date")
    kg_group_ids = fields.Many2many("res.groups", 'kg_groups_rel', string="Access Groups")
    vessel_id = fields.Many2one("sponsor.sponsor", string="Vessel")
    summary = fields.Text(string="Summary")

    @api.constrains('document_type_id', 'document_date', 'validity_start_date', 'validity_end_date',
                    'document_department_id', 'country_id', 'counter_party_id', 'document_company_id')
    def get_file_name(self):
        for rec in self:
            if rec.validity_start_date and rec.validity_end_date and rec.document_date and rec.document_type_id and rec.document_company_id and rec.document_department_id and rec.country_id and rec.counter_party_id:
                rec.name = str(rec.validity_start_date) + '_' + str(rec.validity_end_date) + '-' + str(
                    rec.document_date) + '_' + str(rec.document_type_id.name) + '_' + str(
                    rec.document_company_id.name) + '_' + str(rec.document_department_id.name) + '_' + str(
                    rec.country_id.name) + '_' + str(rec.counter_party_id.name)
            else:
                rec.name = rec.name

    def write(self, vals):
        for rec in self:
            values = ['partner_id', 'name', 'owner_id', 'folder_id', 'tag_ids', 'file_user_ids', 'document_type_id',
                      'document_date', 'validity_start_date', 'validity_end_date', 'document_department_id',
                      'country_id', 'counter_party_id', 'original_file_name', 'upload_date', 'document_company_id']

            if rec.lock_uid and any(field in vals for field in values):
                raise ValidationError("You cannot change on a locked document.")

        return super(KGDocumentsDocumentInherit, self).write(vals)

    def toggle_lock(self):
        if self.is_locked and self.lock_uid and self.lock_uid != self.env.user:
            raise ValidationError("You cannot unlock this document!")
        return super(KGDocumentsDocumentInherit, self).toggle_lock()

    def action_preview(self):
        self.ensure_one()
        attachment = self.env['ir.attachment'].sudo().search([('res_model', '=', self._name), ('res_id', '=', self.id)],
                                                             limit=1)
        if attachment:
            timestamp = int(time.time())
            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/{attachment.id}?download=false&_ts={timestamp}',
                'target': 'new',
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'No Document Found',
                    'message': 'No attachment found for preview.',
                    'type': 'warning',
                    'sticky': False,
                }
            }

    def action_file_access(self):
        users = self.view_user_ids | self.file_user_ids
        folder_group_ids = self.folder_id.folder_group_ids
        groups = self.kg_group_ids | folder_group_ids
        return {
            'name': 'File Access',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'document.access.wizard',
            'target': 'new',
            'context': {
                'default_document_id': self.id,
                'default_current_access_users': [(6, 0, users.ids)],
                'default_file_access_users': [(6, 0, self.file_user_ids.ids)],
                'default_file_groups_access': [(6, 0, groups.ids)],
            },
        }

    @api.depends('folder_id', 'folder_id.folder_group_ids.users')
    def compute_view_users(self):
        for rec in self:
            rec.view_user_ids = False
            if rec.folder_id and rec.folder_id.folder_group_ids:
                user_ids = rec.folder_id.folder_group_ids.mapped('users')
                if user_ids:
                    rec.view_user_ids = [(6, 0, user_ids.ids)]

    def _compute_is_locked(self):
        for record in self:
            record.is_locked = record.lock_uid

    @api.model_create_multi
    def create(self, vals_list):
        res = super(KGDocumentsDocumentInherit, self).create(vals_list)
        if res and res.name:
            res.original_file_name = res.name
            res.upload_date = fields.Date.today()
        if res and res.folder_id and res.folder_id.is_notification and res.folder_id.folder_group_ids:
            users = res.folder_id.folder_group_ids.mapped('users') - self.env.user
            if users:
                document_ids = self.env['ir.attachment'].search(
                    [('res_id', '=', res.id), ('res_model', '=', 'documents.document')], limit=1)
                for user in users:
                    email_subject = f"Document Uploaded : {res.name}"
                    email_body = _(
                        "<p>Dear {user},<br/> "
                        "A new document named <strong>{name}</strong> has been uploaded to the <strong>{workspace}</strong> workspace by {requester}."
                        "<p>Best Regards,<br/>{requester}.</p>"
                    ).format(
                        user=user.name,
                        name=res.name,
                        requester=self.env.user.name,
                        workspace=res.folder_id.name
                    )

                    mail_values = {
                        'subject': email_subject,
                        'body_html': email_body,
                        'email_to': user.email,
                        'author_id': self.env.user.partner_id.id,
                        'model': 'documents.document',
                        'res_id': res.id,
                        'attachment_ids': [(6, 0, document_ids.ids)] if document_ids else None,
                    }

                    mail = self.env['mail.mail'].sudo().create(mail_values)
                    mail.sudo().send()
        return res
