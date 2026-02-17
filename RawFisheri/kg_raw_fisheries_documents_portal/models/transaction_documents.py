import time

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class TransactionDocuments(models.Model):
    _name = "transaction.documents"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Transaction Documents"

    name = fields.Char(string="Reference", copy=False)
    partner_id = fields.Many2one("res.partner", string="Customer", tracking=True, domain=[('customer_rank', '>', 0)])
    date = fields.Date(string="Date", default=fields.Date.context_today, tracking=True)
    type_id = fields.Many2one("transaction.documents.type", tracking=True)
    state = fields.Selection([('draft', 'Draft'), ('submit', 'Submitted'), ('cancel', 'Cancelled')], default='draft',
                             copy=False, string="State", tracking=True)
    file = fields.Binary(string="File")
    filename = fields.Char(string="File Name")
    user_id = fields.Many2one("res.users", string="Created User", default=lambda self: self.env.user, tracking=True)
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company, tracking=True)
    doc_line_ids = fields.One2many("transaction.documents.line", "transaction_document_id", string="Files")
    files_ref = fields.Html(string="Files Reference", compute="compute_files_ref", store=True)

    assignees_ids = fields.Many2many("res.users", string="Assignees")

    @api.depends('doc_line_ids.name', 'doc_line_ids.filename')
    def compute_files_ref(self):
        for rec in self:
            rec.files_ref = False
            if rec.doc_line_ids:
                grouped_data = {}

                for line in rec.doc_line_ids:
                    if line.filename and line.name:
                        raw_names = line.name.split(",")
                        clean_names = [n.strip() for n in raw_names if n.strip() and n.strip().lower() != "unnamed"]
                        if clean_names:
                            grouped_data.setdefault(line.filename, []).extend(clean_names)

                result = ""
                for filename, references in grouped_data.items():
                    result += f"<b>{filename}</b><br/>"
                    for idx, ref in enumerate(references, start=1):
                        result += f"&nbsp;&nbsp;&nbsp;&nbsp;{idx}. {ref}<br/>"
                    result += "<br/>"

                rec.files_ref = result.strip()

    @api.model_create_multi
    def create(self, vals):
        for i in vals:
            i['name'] = self.env['ir.sequence'].next_by_code('transaction.doc.seq')
        return super(TransactionDocuments, self).create(vals)

    def action_submit(self):
        if not self.doc_line_ids:
            raise ValidationError("File upload is required before submission !")
        if not self.partner_id.email:
            raise ValidationError(
                f"Configure the email address for partner {self.partner_id.name} in the customer profile !")

        user_id = self.env['res.users'].search([('partner_id', '=', self.partner_id.id)])
        if not user_id and self.partner_id.customer_rank > 0:
            user = self.env['res.users'].create({
                'name': self.partner_id.name,
                'partner_id': self.partner_id.id,
                'groups_id': self.env.ref('base.group_portal'),
                'login': self.partner_id.email
            })
            if user:
                user.action_reset_password()

        file_details = """
        <table border="1" cellspacing="0" cellpadding="5" style="border-collapse: collapse; margin-left:20px;">
            <thead>
                <tr align="center">
                    <th style="border: 1px solid black;">Reference</th>
                    <th style="border: 1px solid black;">File Name</th>
                    <th style="border: 1px solid black;">Type</th>
                    <th style="border: 1px solid black;">Status</th>
                </tr>
            </thead>
            <tbody>
        """

        for line in self.doc_line_ids:
            approval_note = "Waiting for Approval" if line.must_be_approved else "No Approval Needed"
            file_details += f"""
                <tr>
                    <td style="border: 1px solid black;">{line.name if line.name else ''}</td>
                    <td style="border: 1px solid black;">{line.filename}</td>
                    <td style="border: 1px solid black;">{line.type_id.name}</td>
                    <td style="border: 1px solid black;">{approval_note}</td>
                </tr>
            """

        file_details += """
            </tbody>
        </table>
        """

        email_subject = f"Documents Uploaded - Reference: {self.name}"

        email_body = _(
            "<p>Dear {customer},</p>"
            "<p>The following documents have been uploaded by {requester}:</p>"
            "{file_list}<br/>"
            "<p>Best Regards,<br/>{requester}</p>"
        ).format(
            customer=self.partner_id.name,
            requester=self.env.user.name,
            reference=self.name,
            file_list=file_details,
        )

        mail_values = {
            'subject': email_subject,
            'body_html': email_body,
            'email_to': self.partner_id.email,
            'author_id': self.env.user.partner_id.id,
            'model': 'transaction.documents',
            'res_id': self.id,
        }

        mail = self.env['mail.mail'].sudo().create(mail_values)
        mail.sudo().send()

        self.state = 'submit'

    def action_cancel(self):
        self.state = 'cancel'

    def action_draft(self):
        self.state = 'draft'

    def action_preview(self):
        if self.file:
            timestamp = int(time.time())
            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/{self._name}/{self.id}/file?download=false&_ts={timestamp}',
                'target': 'new',
            }


class TransactionDocumentsLine(models.Model):
    _name = "transaction.documents.line"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Transaction Documents Line"

    name = fields.Char(string="Reference", copy=False)
    type_id = fields.Many2one("transaction.documents.type", tracking=True)
    file = fields.Binary(string="File")
    filename = fields.Char(string="File Name")
    transaction_document_id = fields.Many2one("transaction.documents", string="Transaction Document")
    must_be_approved = fields.Boolean(default=False, string="Must Be Approved")
    status = fields.Selection([('draft', 'Draft'),
        ('no_need_approve', 'No Need to Approve'),
        ('waiting_for_approve', 'Waiting for Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string="Status", default='no_need_approve', copy=False)
    partner_id = fields.Many2one("res.partner", string="Customer", related='transaction_document_id.partner_id',
                                 domain=[('customer_rank', '>', 0)])
    state = fields.Selection([('draft', 'Draft'), ('submit', 'Submitted'), ('cancel', 'Cancelled')], default='draft',
                             copy=False, string="State", related='transaction_document_id.state')
    reject_reason = fields.Char(string="Reject Reason")

    def action_set_to_draft(self):
        self.status = 'draft'

    @api.onchange('must_be_approved')
    def mark_approve(self):
        for rec in self:
            if rec.must_be_approved:
                rec.status = 'waiting_for_approve'
            else:
                rec.status = 'no_need_approve'

    def action_approve(self):
        self.status = 'approved'

    def action_reject(self):
        return {
            'name': 'Reject Reason',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'td.reject.reason.wizard',
            'target': 'new',
            'context': {
                'default_td_id': self.transaction_document_id.id,
                'default_td_line_id': self.id,
            },
        }

    def action_resend(self):
        for rec in self:
            subject = _("Document Re-uploaded: %s") % (rec.name or "Document")
            body = _(
                "<p>Dear %s,</p>"
                "<p>The rejected document <b>%s</b> has been re-uploaded.</p>"
                "<p>Previous rejection reason:</p>"
                "<blockquote>%s</blockquote>"
                "<p>Please review the updated document.</p>"
                "<p>Regards,<br/>%s</p>"
            ) % (
                       rec.partner_id.name or "Customer",
                       rec.name or "",
                       rec.reject_reason or _("No reason specified"),
                       rec.transaction_document_id.user_id.name or self.env.user.name,
                   )

            mail_values = {
                'subject': subject,
                'body_html': body,
                'email_from': rec.transaction_document_id.user_id.email or rec.env.user.email,
                'email_to': rec.partner_id.email or rec.env.user.email,
            }
            self.env['mail.mail'].sudo().create(mail_values).send()
            rec.status = 'waiting_for_approve'



