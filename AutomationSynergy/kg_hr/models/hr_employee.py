# -*- coding: utf-8 -*-
from datetime import timedelta, date

from odoo import fields, models, _, api
from odoo.exceptions import ValidationError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    bank_name = fields.Char(string=" Bank Name")
    iban = fields.Char(string="IBAN")
    bic = fields.Char(string="BIC(Swift code)")
    medical = fields.Binary(string="Medical")
    civilid = fields.Binary(string="Civil ID")
    employee_contract = fields.Binary(string="Employee contract")
    clearance_certificate = fields.Binary(string="Clearance Certificate")
    join_date = fields.Date(string='Joining Date')
    passport_exp_date = fields.Date(string='Passport Expiry Date')
    date_relieve = fields.Date(string='Relieve Date')
    visa_uid_no = fields.Char(string="Visa/UID No")
    visa_emirate = fields.Char(string="Visa Emirate")
    emirate_no = fields.Char(string="Emirate No")
    emp_civil_no = fields.Char(string="Employee Civil Number")
    personal_no = fields.Char('Personal NO.')
    employee_id = fields.Char('Employee ID(Jafza)')

    probation_period_length = fields.Selection([
        ('3', '3 Months'),
        ('6', '6 Months')
    ], string="Probation Period ", default='3')
    probation_end_date = fields.Date(string="Probation End Date", compute='_compute_probation_end_date', store=True)
    probation_completed = fields.Boolean(string="Probation Completed", default=False)
    state = fields.Selection([('probation', 'Probation'), ('permanent', 'Permanent')], string='Status',
                             default='probation', required=True)
    airticket_id = fields.Many2one('airticket.master', 'Air Ticket')

    @api.depends('join_date', 'probation_period_length')
    def _compute_probation_end_date(self):
        for employee in self:
            if employee.join_date and employee.probation_period_length:
                probation_length = int(employee.probation_period_length)
                employee.probation_end_date = employee.join_date + timedelta(days=probation_length * 30)
            else:
                employee.probation_end_date = False

    @api.model
    def _check_probation_period(self):
        today = date.today()
        employees = self.search([
            ('probation_end_date', '<=', today),
            ('probation_completed', '=', False),
        ])

        for employee in employees:
            employee.probation_completed = True
            employee.state = 'permanent'
            self._send_probation_completion_email(employee)

    def _send_probation_completion_email(self, employee):
        mail_content = f"""
                <p>Dear {employee.name},</p>
                <p>Congratulations! Your probation period has been successfully completed as of today.</p>
                <p>Thank you for your hard work and dedication.</p>
                <p>Best regards,</p>
                <p>{employee.company_id.name}</p>
            """
        subject = 'Your Probation Period is Complete'
        main_content = {
            'subject': subject,
            'author_id': self.env.user.partner_id.id,
            'body_html': mail_content,
            'email_to': employee.work_email,
        }
        self.env['mail.mail'].create(main_content).send()


class ResBank(models.Model):
    """inherited to add field"""
    _inherit = 'res.bank'

    routing_code = fields.Char(string="Routing Code", size=9, required=True, help="Bank Route Code")
