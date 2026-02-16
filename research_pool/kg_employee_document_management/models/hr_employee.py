# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import fields, models, _
from odoo.exceptions import ValidationError

class HrEmployee(models.Model):

    _inherit = 'hr.employee'


    document_ids = fields.One2many('hr.employee.document','document_id',string="Document")

    def mail_reminder(self):
        """Sending document expiry notification to employees."""
        for employee in self.search([]):
            document_types = set(
                document.document_type_id for document in employee.document_ids if document.expiry_date)
            for doc_type in document_types:
                document_table = f'<table border="1"><tr><th>Employee Name</th><th>Expiry Date</th><th>Document Number</th></tr>'
                for document in employee.document_ids.filtered(
                        lambda d: d.document_type_id == doc_type and d.expiry_date):
                    exp_date = fields.Date.from_string(document.expiry_date)
                    days_before = timedelta(days=document.before_days or 0)
                    is_expiry_today = fields.Date.today() == exp_date
                    is_notification_day = any([
                        document.notification_type == 'single' and is_expiry_today,
                        document.notification_type == 'multi' and (
                                fields.Date.today() == fields.Date.from_string(
                            document.expiry_date) - days_before or is_expiry_today),
                        document.notification_type == 'everyday' and fields.Date.today() >= fields.Date.from_string(
                            document.expiry_date) - days_before,
                        document.notification_type == 'everyday_after' and fields.Date.today() <= fields.Date.from_string(
                            document.expiry_date) + days_before,
                        not document.notification_type and fields.Date.today() == fields.Date.from_string(
                            document.expiry_date) - timedelta(days=7)
                    ])

                    if is_notification_day:
                        document_table += f'<tr><td>{document.employee_ref_id.name}</td><td>{document.expiry_date}</td><td>{document.name}</td></tr>'

                document_table += '</table>'

                if document_table != '<table border="1"><tr><th>Employee Name</th><th>Expiry Date</th><th>Document Number</th></tr></table>':
                    employee_name = employee.name
                    mail_content = (
                        f"Hello {employee_name},<br>Your following {doc_type.name} documents are going to expire soon:<br>{document_table}"
                        "Please renew them before the expiry date."
                    )
                    subject = _('Documents Expiry Reminder')
                    main_content = {
                        'subject': subject,
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': employee.work_email,
                    }
                    self.env['mail.mail'].create(main_content).send()


