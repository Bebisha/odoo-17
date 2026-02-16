# -*- coding: utf-8 -*-

from datetime import date, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from collections import defaultdict


class HrEmployeeDocument(models.Model):
    _name = 'hr.employee.document'
    _description = 'HR Employee Documents'

    name = fields.Char(string='Document Number', required=True, copy=False,
                       help='You can give your Document number.')
    description = fields.Text(string='Description', copy=False,
                              help="Description of the documents.")
    expiry_date = fields.Date(string='Expiry Date', copy=False,
                              help="Expiry date of the documents.")
    document_id = fields.Many2one('hr.employee', string="Document")
    employee_ref_id = fields.Many2one('hr.employee', help='Specify the employee name.', compute='default_employee',readonly=False, string="Employee")

    @api.depends('document_id')
    def default_employee(self):
        # Add your logic here to determine the default employee

        record = self.document_id
        for rec in record:
            print(rec)
            if rec:
                self.write({
                    'employee_ref_id':rec.id
                })
            else:
                self.write({
                    'employee_ref_id': False
                })

        # return rec
        # return self.document_id._orgin.id

    doc_attachment_ids = fields.Many2many('ir.attachment',
                                          'doc_attach_rel',
                                          'doc_id', 'attach_id3',
                                          string="Attachment",
                                          help='You can attach the copy of your'
                                               ' document', copy=False)
    issue_date = fields.Date(string='Issue Date', default=fields.datetime.now(),
                             help="Date of issued", copy=False)
    document_type_id = fields.Many2one('document.type',
                                       string="Document Type",
                                       help="Type of the document.")
    before_days = fields.Integer(string="Days",
                                 help="How many number of days before to get "
                                      "the notification email.")
    notification_type = fields.Selection([
        ('single', 'Notification on expiry date'),
        ('multi', 'Notification before few days'),
        ('everyday', 'Everyday till expiry date'),
        ('everyday_after', 'Notification on and after expiry')
    ], string='Notification Type',
        help="Select type of the documents expiry notification.")

    attachment_filename = fields.Char(string="Attachment Filename", compute='_compute_attachment_data', store=True)

    download_link = fields.Char(string="Download Link", compute='_compute_download_attachment_data', store=True)

    @api.depends('doc_attachment_ids')
    def _compute_attachment_data(self):
        print(self.document_id._origin)
        print(self.employee_ref_id, 'employee_ref_id')
        for employee in self:
            attachment = employee.doc_attachment_ids
            if attachment:
                employee.attachment_filename = attachment.name
                # employee.download_link = '/web/content/%s?download=true' % attachment.id

    @api.depends('doc_attachment_ids')
    def _compute_download_attachment_data(self):
        for employee_doc in self:
            download_links = []
            base_download_link = '/web/content/%s?download=true'
            for attachment in employee_doc.doc_attachment_ids:
                download_links.append(base_download_link % attachment.id)
            employee_doc.download_link = ",".join(download_links)

    @api.constrains('expiry_date')
    def _check_expiry_date(self):
        """This method is called as a constraint whenever the 'expiry_date'
         field of an 'hr.employee.document' record is modified."""
        for rec in self:
            if rec.expiry_date:
                exp_date = fields.Date.from_string(rec.expiry_date)
                if exp_date < date.today():
                    raise UserError(_('Your Document Is Expired.'))

    def hr_mail_reminder(self):
        """Sending document expiry notification to HR employees."""
        hr_department = self.env.ref('hr.group_hr_manager')
        if hr_department:
            expired_records = self.search([('expiry_date', '!=', False)])
            if expired_records:
                # Group expired records by document type
                documents_by_type = defaultdict(list)
                for record in expired_records:
                    documents_by_type[record.document_type_id.name].append(record)

                # Construct table for each document type
                document_tables = []
                for doc_type, records in documents_by_type.items():
                    document_table_rows = []
                    for record in records:
                        exp_date = fields.Date.from_string(record.expiry_date)
                        days_before = timedelta(days=record.before_days or 0)
                        is_expiry_today = fields.Date.today() == exp_date
                        is_notification_day = any([
                            record.notification_type == 'single' and is_expiry_today,
                            record.notification_type == 'multi' and (
                                    fields.Date.today() == fields.Date.from_string(record.expiry_date) - days_before or
                                    is_expiry_today
                            ),
                            record.notification_type == 'everyday' and (
                                    fields.Date.today() >= fields.Date.from_string(record.expiry_date) - days_before
                            ),
                            record.notification_type == 'everyday_after' and (
                                    fields.Date.today() <= fields.Date.from_string(record.expiry_date) + days_before
                            ),
                            not record.notification_type and (
                                    fields.Date.today() == fields.Date.from_string(record.expiry_date) - timedelta(
                                days=7)
                            )
                        ])
                        if is_notification_day:
                            employee_name = record.employee_ref_id.name
                            expiry_date_str = str(record.expiry_date)
                            document_name = record.name
                            document_table_rows.append(
                                f'<tr><td>{employee_name}</td><td>{expiry_date_str}</td><td>{document_name}</td><td>{doc_type}</td></tr>'
                            )
                    if document_table_rows:
                        document_table = f'<h2>{doc_type}</h2>'
                        document_table += '<table border="1"><tr><th>Employee Name</th><th>Expiry Date</th><th>Document Number</th><th>Document Type</th></tr>'
                        document_table += ''.join(document_table_rows)
                        document_table += '</table>'
                        document_tables.append(document_table)

                # Construct email content
                mail_content = "Hello,<br>The following documents have expired:<br>"
                mail_content += "<br>".join(document_tables)
                mail_content += "<br>Please take necessary action."

                subject = _('Documents Expiry Reminder')

                main_content = {
                    'subject': subject,
                    'author_id': self.env.user.partner_id.id,
                    'body_html': mail_content,
                    'email_to': ','.join(hr_department.users.mapped('work_email')),
                }
                self.env['mail.mail'].create(main_content).send()
    def demo(self):
        print('lllllllllll')