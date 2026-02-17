# -*- coding: utf-8 -*-

from datetime import date

from bs4 import BeautifulSoup
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _


class KGHrEmployee(models.Model):
    _inherit = 'hr.employee'

    sponsor_name = fields.Many2one('sponsor.sponsor', 'Vessel')
    employees_type = fields.Selection([
        ('omani', 'Omani employees'),
        ('contractors', 'Contractors'),
        ('expats', 'Expats'),
    ], string='Employee Types', default='omani')
    employee_status = fields.Selection([
        ('active', 'Active'),
        ('not_active', 'Inactive'),
    ], string='Employee Status', default='active')
    coach_id = fields.Many2one(
        'hr.employee', 'Coach', readonly=False, check_company=True)
    factory_manager_ids = fields.Many2many(
        'hr.employee', 'factory_manager', 'fm_column1', string='Factory Manager', readonly=False, check_company=True)
    employee_no = fields.Char(string='Employee No.', default=lambda self: _('New'))
    employee_id_no = fields.Char(string='Employee ID No.')
    employee_file_no = fields.Char(string='Employee File No.')
    date_of_joining = fields.Date(string='Date of Joining')
    sign_on_date = fields.Date(string='Sign On Date', compute="compute_sign_on")
    sign_off_date = fields.Date(string='Sign Off Date', compute="compute_sign_off")
    employee_id_issue_date = fields.Date(string='Employee ID Issue Date')
    employee_id_expiry_date = fields.Date(string='Employee ID Expiry Date')
    employee_passport_issue_date = fields.Date(string='Employee Passport Issue Date')
    employee_passport_expiry_date = fields.Date(string='Employee Passport Expiry Date')
    employee_medical_expiry_date = fields.Date(string='Employee Medical Expiry Date')
    seaman_book_expiry_date = fields.Date(string="Seaman's Book Expiry Date")
    work_location = fields.Char(string='Site')
    crew = fields.Boolean(string='Is Crew Member?')
    years_of_service = fields.Char(string='Years Of Service', compute='_compute_years_of_service')
    check_access_team_id = fields.Boolean('Check Access', compute='_compute_access_contract')
    restrict_editing = fields.Boolean('restrict Manger')
    check_manager = fields.Boolean('Check Manger', compute='_compute_check_manager')
    current_user = fields.Many2one('res.users')
    manager_ids = fields.Many2many('hr.employee', 'rel_id', 'man_col_1', string='Managers', store=True, readonly=False,
                                   check_company=True)
    agency = fields.Char(string='Agency')

    def compute_sign_on(self):
        for rec in self:
            rec.sign_on_date = False
            sign_on_id = self.env['sign.on.off'].search([('employee_id', '=', rec.id), ('state', '=', 'approved')],
                                                        order='id desc', limit=1)
            rec.sign_on_date = sign_on_id.sign_on if sign_on_id else False

    def compute_sign_off(self):
        for rec in self:
            rec.sign_off_date = False
            sign_off_id = self.env['sign.on.off'].search([('employee_id', '=', rec.id), ('state', '=', 'approved')],
                                                          order='id desc', limit=1)
            rec.sign_off_date = sign_off_id.sign_off if sign_off_id else False

    @api.depends('user_id')
    def _compute_access_contract(self):
        for rec in self:
            rec.check_access_team_id = self.env.user.id in rec.manager_ids.mapped('user_id.id')

    @api.depends('parent_id')
    def _compute_check_manager(self):
        for rec in self:
            if rec.parent_id.restrict_editing and not self.env.user.has_group('hr.group_hr_manager'):
                rec.check_manager = True
            else:
                rec.check_manager = False
            # rec.check_manager = self.env.user.has_group('hr_contract.group_hr_contract_manager')

    @api.model
    def create(self, vals):
        """ Employee Sequence Number Generation """
        if vals.get('employee_no', _('New')) == _('New'):
            vals['employee_no'] = self.env['ir.sequence'].next_by_code(
                'employee.no.sequence') or _('New')
        return super(KGHrEmployee, self).create(vals)

    @api.depends('date_of_joining')
    def _compute_years_of_service(self):
        """To compute the years of service"""
        for record in self:
            if record.date_of_joining:
                joining_date = fields.Date.from_string(record.date_of_joining)
                today = date.today()
                delta = relativedelta(today, joining_date)

                years = delta.years
                months = delta.months
                days = delta.days

                parts = []
                if years:
                    parts.append(f"{years} year{'s' if years > 1 else ''}")
                if months:
                    parts.append(f"{months} month{'s' if months > 1 else ''}")
                if days:
                    parts.append(f"{days} day{'s' if days > 1 else ''}")

                record.years_of_service = ', '.join(parts)
            else:
                record.years_of_service = 'N/A'

    @api.depends('parent_id')
    def _compute_coach(self):
        """To override computation for coach field"""
        pass

    @api.model
    def _check_employee_status(self):
        """To update the Employee Status"""
        employees = self.search([])
        today = fields.Date.today()
        for employee in employees:
            if not employee.contract_id:
                employee.write({'employee_status': 'not_active'})
            else:
                employee.write({'employee_status': 'active'})

    def resigned_employees_pdf(self):
        """ PDF report for resigned employees """
        values = []
        for rec in self:
            departure_description_html = rec.departure_description
            departure_description_text = BeautifulSoup(departure_description_html, 'html.parser').get_text()
            vals = {
                'employee': rec.name,
                'employee_no': rec.employee_no,
                'department': rec.department_id.name,
                'job': rec.job_id.name,
                'departure_reason_id': rec.departure_reason_id.name,
                'departure_description': departure_description_text,
                'date_of_joining': rec.date_of_joining,
                'years_of_service': rec.years_of_service,
                'departure_date': rec.departure_date
            }
            values.append(vals)

        data = {
            'company_id': self.env.user.company_id.name,
            'value_list': values,
        }

        return self.env.ref('kg_raw_fisheries_hrms.action_report_resigned_employees_pdf').report_action(self, data=data)

    def action_update_passport_expiry(self, new_date=False):
        for employee in self:
            if new_date:
                employee.passport_expiry_notification = False
                employee.employee_passport_expiry_date = new_date


class KGEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    sponsor_name = fields.Many2one('sponsor.sponsor', 'Sponsor')
    employees_type = fields.Selection([
        ('omani', 'Omani employees'),
        ('contractors', 'Contractors'),
        ('expats', 'Expats'),
    ], string='Employee Types')
    employee_status = fields.Selection([
        ('active', 'Active'),
        ('not_active', 'Inactive'),
    ], string='Employee Status', default='active')
    employee_no = fields.Char(string='Employee No.')
    employee_id_no = fields.Char(string='Employee ID No.')
    employee_file_no = fields.Char(string='Employee File No.')
    date_of_joining = fields.Date(string='Date of Joining')
    sign_on_date = fields.Date(string='Sign On Date')
    sign_off_date = fields.Date(string='Sign Off Date')
    employee_id_issue_date = fields.Date(string='Employee ID Issue Date')
    employee_id_expiry_date = fields.Date(string='Employee ID Expiry Date')
    employee_passport_issue_date = fields.Date(string='Employee Passport Issue Date')
    employee_passport_expiry_date = fields.Date(string='Employee Passport Expiry Date')
    work_location = fields.Char(string='Site')
    crew = fields.Boolean(string='Is Crew Member?')
    years_of_service = fields.Char(string='Years Of Service', readonly=True, compute='_compute_years_of_service')
    factory_manager_ids = fields.Many2many(
        'hr.employee.public', 'factory_manager', string='Factory Manager', readonly=True, check_company=True)
    check_access_team_id = fields.Boolean('Check Access', compute='_compute_access_contract')
    check_manager = fields.Boolean('Check Manger')
    current_user = fields.Many2one('res.users')
    restrict_editing = fields.Boolean('restrict Manger')
    manger_ids = fields.Many2many('hr.employee', 'rel_id', 'man_col_1', string='Managers', store=True, readonly=False,
                                  check_company=True)

    @api.depends('date_of_joining')
    def _compute_years_of_service(self):
        pass;

    def _compute_access_contract(self):
        pass;
