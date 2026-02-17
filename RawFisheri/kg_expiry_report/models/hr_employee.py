# -*- coding: utf-8 -*-
import json

from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    passport_expiry_notification = fields.Boolean(string='Passport Expiry Notification')
    seamans_book_expiry_notification = fields.Boolean(string="Seaman's Book Expiry Notification")

    def _send_passport_expiry_notification(self):
        """ To send passport expiry notification nine months before expiry """
        employees = self.search([])
        today = fields.Date.today()
        nine_months_later = today + relativedelta(months=9)

        for employee in employees:
            if not employee.passport_expiry_notification and employee.employee_passport_expiry_date and today <= employee.employee_passport_expiry_date <= nine_months_later:
                group_send_mail = []
                config_recs = self.env['ir.config_parameter'].sudo().get_param(
                    'kg_expiry_report.passport_expiry_notification_employee_ids', False)
                employee_ids = json.loads(config_recs)
                employees_list = self.env['hr.employee'].browse(employee_ids)
                for config_rec in employees_list:
                    if config_rec.work_email:
                        group_send_mail.append(config_rec.work_email)

                if group_send_mail:
                    subject = _('Passport Expiry')
                    body = _(
                        "<p>Dear Sir/Ma'am,</p>"
                        "<p>This is to inform you that the passport of <strong>{employee_name}</strong> is set to expire in nine months.</p>"
                        "<p><strong>Expiry Date: {expiry_date}</strong></p>"
                        "<p>Please review and take the necessary actions.</p>"
                        "<p>Thank you.</p>"
                    ).format(
                        employee_name=employee.name,
                        expiry_date=employee.employee_passport_expiry_date,
                    )
                    mail_values = {
                        'subject': subject,
                        'body_html': body + "<br/>",
                        'email_to': ', '.join(group_send_mail),
                    }
                    self.env['mail.mail'].sudo().create(mail_values).send()
                    employee.write({
                        'passport_expiry_notification': True
                    })

    def _send_seamans_book_expiry_notification(self):
        """ To send seaman's book expiry notification three months before expiry """
        employees = self.search([])
        today = fields.Date.today()
        three_months_later = today + relativedelta(months=3)

        for employee in employees:
            if not employee.seamans_book_expiry_notification and employee.seaman_book_expiry_date and today <= employee.seaman_book_expiry_date <= three_months_later:
                group_send_mail = []
                config_recs = self.env['ir.config_parameter'].sudo().get_param(
                    'kg_expiry_report.seamans_expiry_notification_employee_ids', False)
                employee_ids = json.loads(config_recs)
                employees_list = self.env['hr.employee'].browse(employee_ids)
                for config_rec in employees_list:
                    if config_rec.work_email:
                        group_send_mail.append(config_rec.work_email)

                if group_send_mail:
                    subject = _("Seaman's Book Expiry")
                    body = _(
                        "<p>Dear Sir/Ma'am,</p>"
                        "<p>This is to inform you that the seaman's book of <strong>{employee_name}</strong> is set to expire in nine months.</p>"
                        "<p><strong>Expiry Date: {expiry_date}</strong></p>"
                        "<p>Please review and take the necessary actions.</p>"
                        "<p>Thank you.</p>"
                    ).format(
                        employee_name=employee.name,
                        expiry_date=employee.seaman_book_expiry_date,
                    )
                    mail_values = {
                        'subject': subject,
                        'body_html': body + "<br/>",
                        'email_to': ', '.join(group_send_mail),
                    }
                    self.env['mail.mail'].sudo().create(mail_values).send()
                    employee.write({
                        'seamans_book_expiry_notification': True
                    })

    def get_seamans_data(self):
        """To get the seaman's book expiry data """
        today = fields.Date.today()
        three_months_later = today + relativedelta(months=3)
        employees = self.env['hr.employee'].search([('seaman_book_expiry_date', '<=', three_months_later)])

        vessels = {}
        for employee in employees:
            vessel_id = employee.sponsor_name.id
            vessel_name = employee.sponsor_name.name or 'Unknown'

            if vessel_id not in vessels:
                vessels[vessel_id] = {
                    'vessel': vessel_name,
                    'employees': []
                }

            employee_data = {
                'name': employee.name,
                'id': employee.id,
                'job_title': employee.job_id.name,
                'date_start': employee.contract_id.date_start,
                'date_end': employee.contract_id.date_end,
                'seaman_book_expiry_date': employee.seaman_book_expiry_date,
            }
            vessels[vessel_id]['employees'].append(employee_data)

        result = list(vessels.values())

        return {
            'vessels_by_department': result,
        }

    def get_passport_data(self):
        """To get the passport expiry data """

        today = fields.Date.today()
        nine_months_later = today + relativedelta(months=9)
        employees = self.env['hr.employee'].search([('employee_passport_expiry_date', '<=', nine_months_later)])

        vessels_by_department = {}
        for employee in employees:
            vessel_id = employee.sponsor_name.id
            department_id = employee.department_id.id
            vessel_name = employee.sponsor_name.name or 'Unknown'
            department_name = employee.department_id.name or 'Unknown'

            if vessel_id not in vessels_by_department:
                vessels_by_department[vessel_id] = {
                    'vessel': vessel_name,
                    'departments': {}
                }

            if department_id not in vessels_by_department[vessel_id]['departments']:
                vessels_by_department[vessel_id]['departments'][department_id] = {
                    'department': department_name,
                    'employees': [],
                }

            employee_data = {
                'name': employee.name,
                'id': employee.id,
                'job_title': employee.job_id.name,
                'date_start': employee.contract_id.date_start,
                'date_end': employee.contract_id.date_end,
                'employee_passport_expiry_date': employee.employee_passport_expiry_date,
            }
            vessels_by_department[vessel_id]['departments'][department_id]['employees'].append(employee_data)

        result = []
        for vessel_data in vessels_by_department.values():
            departments_list = []
            for department_data in vessel_data['departments'].values():
                departments_list.append({
                    'department': department_data['department'],
                    'employees': department_data['employees'],
                })
            result.append({
                'vessel': vessel_data['vessel'],
                'departments': departments_list,
            })
        return {
            'vessels_by_department': result,
        }
