# -*- coding: utf-8 -*-

from odoo import models, api, fields
from datetime import datetime, timedelta


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    employee_no = fields.Char('Employee Number', default='New')
    date_joining = fields.Date('Date of Joining')
    project_team_id = fields.Many2one('project.team', string="Project Team")
    employee_id = fields.Char(string="Employee ID", readonly=True, copy=False)

    country_code_ssnid = fields.Char(related="company_id.country_code", string='SSNID')
    early_late_approve_ids = fields.Many2many(
        'res.users',
        'early_id',  # The intermediate table name
        'model_id',  # The column in the intermediate table that refers to your model (the left side)
        'user_id',  # The column in the intermediate table that refers to the 'res.users' model (the right side)
        string="Early/Late"
    )
    hr_manager_ids = fields.Many2many('hr.employee', string='HR manager', copy=False, column1='cc_add_hr_manger',
                                      column2='rel_hr_manger', relation="rel_hr_employee")

    designation_id = fields.Many2one('hr.designation', string="Designation")


    def send_birthday_wish(self):
        today_date = datetime.today().date()
        for employee in self.env['hr.employee'].search([]):
            if employee.birthday:
                if today_date.day == employee.birthday.day and today_date.month == employee.birthday.month:
                    hr_managers = employee.hr_manager_ids
                    cc_emails = [manager.work_email for manager in hr_managers if manager.work_email]
                    cc_emails_string = ', '.join(cc_emails)
                    template_id = self.env.ref('kg_hr_employee.email_birthday_wishes_employee_template_')
                    template_id.send_mail(employee.id, force_send=True, email_values={
                        'email_cc': cc_emails_string,
                    })

        for employee in self.env['hr.employee'].search([]):
            if employee.first_contract_date:
                if today_date.day == employee.first_contract_date.day and today_date.month == employee.first_contract_date.month:
                    template_id = self.env.ref('kg_hr_employee.email_work_anniversary_notification_template')
                    template_id.send_mail(employee.id, force_send=True)

    # def _send_allocation_reminder(self):
    #     if self.env.company.country_code in ['AE', 'BH', 'OM']:
    #         print("vvvvvvvvvvvvvvvvvvvvvvvvvvv",self.env.company.country_code)
    #         conf_setting = []
    #         hr_manager_emails = self.env['ir.config_parameter'].sudo().get_param('kg_hr_employee.remainder_mail_ids', False)
    #         if hr_manager_emails:
    #             hr_manager_emails = hr_manager_emails.replace('[', '').replace(']', '')
    #             conf_setting = list(map(int, hr_manager_emails.split(',')))
    #         partners = self.env['res.partner'].search([('user_id', 'in', conf_setting)])
    #         today = fields.Date.today()
    #         employees = self.env['hr.employee'].search([])
    #         for employee in employees:
    #             if employee.date_joining:
    #                 anniversary_date = fields.Date.from_string(employee.date_joining)
    #                 anniversary_last_year = anniversary_date.replace(year=today.year)
    #                 if anniversary_last_year == today - timedelta(days=1):
    #                     for partner in partners:
    #                         email_subject = f"Employee Allocation Reminder: {employee.name}"
    #                         email_body = f"Dear HR Manager,\n\nThis is a reminder that the allocation for the employee {employee.name} who joined on {employee.date_joining} is due to be completed by tomorrow."
    #                         mail_values = {
    #                             'subject': email_subject,
    #                             'body_html': email_body,
    #                             'email_to': partner.email,
    #                         }
    #                         mail = self.env['mail.mail'].create(mail_values)
    #                         mail.send()

    @api.model
    def create(self, vals):
        if vals.get('company_id'):
            company_obj = self.env['res.company'].browse(vals.get('company_id'))
            if company_obj.country_code == 'US':
                vals['employee_id'] = self.env['ir.sequence'].next_by_code('seq_employee_id_us') or 'New'
            elif company_obj.country_code == 'BH':
                vals['employee_id'] = self.env['ir.sequence'].next_by_code('seq_employee_id_bh') or 'New'
            elif company_obj.country_code == 'IN':
                vals['employee_id'] = self.env['ir.sequence'].next_by_code('seq_employee_id_in') or 'New'
            elif company_obj.country_code == 'OM':
                vals['employee_id'] = self.env['ir.sequence'].next_by_code('seq_employee_id_om') or 'New'
            elif company_obj.country_code == 'AE':
                vals['employee_id'] = self.env['ir.sequence'].next_by_code('seq_employee_id_dubai') or 'New'
            else:
                vals['employee_id'] = 'New'
            if vals.get('employee_no', 'New') == 'New':
                if company_obj.employee_sequence_id:
                    vals['employee_no'] = company_obj.employee_sequence_id.next_by_id()

        result = super(HrEmployee, self).create(vals)
        return result

    training_end_date = fields.Date(string="Training End Date", compute="_compute_training_end_date")

    @api.depends('date_joining')
    def _compute_training_end_date(self):
        for employee in self:
            if employee.date_joining:
                employee.training_end_date = employee.date_joining + timedelta(days=6 * 30)

    @api.model
    def _allocate_annual_leave(self):
        today = fields.Date.today()
        employees = self.search([('training_end_date', '!=', False)])
        for employee in employees:
            # Calculate the one-year mark including training
            one_year_after_start = employee.date_joining + timedelta(days=365)

            # Allocate annual leave if 1 year has passed since the start date
            if today >= one_year_after_start:
                self.env['hr.leave.allocation'].create({
                    'employee_ids': employee.id,
                    'holiday_status_id': self.env.ref('hr_holidays.holiday_status_cl').id,  # Annual leave type
                    'number_of_days_display': 30,
                    # 'state': 'validate',
                })


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    employee_no = fields.Char('Employee Number', default='New')
    date_joining = fields.Date('Date of Joining')
    project_team_id = fields.Many2one('project.team', string="Project Team")
    early_late_approve_ids = fields.Many2many(
        'res.users',
        'early_id',  # The intermediate table name
        'model_id',  # The column in the intermediate table that refers to your model (the left side)
        'user_id',  # The column in the intermediate table that refers to the 'res.users' model (the right side)
        string="Early/Late"
    )
    designation_id = fields.Many2one('hr.designation', string="Designation")


class RecCompany(models.Model):
    _inherit = 'res.company'

    employee_sequence_id = fields.Many2one('ir.sequence', 'Employee sequence', help='sequence for employee creation')



# class ResUser(models.Model):
#     _inherit = 'res.users'
#
#     project_team_id = fields.Many2one('project.team', string="Project Team")
