# -*- coding: utf-8 -*-
# from num2words import num2words
from num2words import num2words

from odoo import fields, models, api, _
from datetime import datetime, timedelta, date
import re


class HRResignation(models.Model):
    """ Employee Resignation """
    _name = 'hr.resignation'
    _description = 'hr.resignation'
    _inherit = 'mail.thread'
    _rec_name = 'name'

    name = fields.Char(string='Reference', default=lambda self: _('New'), readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    date_join = fields.Date(string='Date Joining', related='employee_id.date_of_joining')
    employee_no = fields.Char(string='Employee No.', related='employee_id.employee_no')
    job_id = fields.Many2one(string='Designation', related='employee_id.job_id')
    date_last_working = fields.Date(string='Last working day')
    total_service = fields.Char(string='Total No. of Days Working', compute='_compute_total_service')
    contract_id = fields.Many2one('hr.contract', string='Contract', related='employee_id.contract_id')
    working_days = fields.Char(string='Working Days')
    is_pending_sal = fields.Boolean(string='Is pending Sal', compute='_compute_is_pending_sal')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    date_today = fields.Date(string='Date', default=date.today())
    gratuity_amount = fields.Float(string='Gratuity Amount', compute='_compute_calculate_gratuity')
    resignation_line_ids = fields.One2many('hr.resignation.line', 'resignation_id', string='Resignation Lines')
    e_and_d_line_ids = fields.One2many('hr.earn.deduct.line', 'resignation_id', string='Earnings and Deductions Lines')
    pending_salary = fields.Float(string='Pending Salary', compute='_compute_payable')
    annual_leave_pay = fields.Float(string='Annual Leave Pay', compute='_compute_payable')
    pending_leave_sal_days = fields.Float(string='Pending Annual Leave Days')
    total_payable_ot_hours = fields.Float(string='Total Payable OT Hours')

    @api.model
    def create(self, vals):
        """ Employee resignation sequence number"""
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'resignation.sequence') or _('New')
        return super(HRResignation, self).create(vals)

    @api.model
    def get_amount_in_words(self, amount):
        amount_in_words = num2words(amount, lang='en')
        return amount_in_words.capitalize()

    @api.depends('date_join', 'date_last_working')
    def _compute_total_service(self):
        """ Compute employee total service in days """
        for resignation in self:
            if resignation.date_join and resignation.date_last_working:
                date_join = resignation.date_join
                date_last_working = resignation.date_last_working
                total_days = (date_last_working - date_join).days
                resignation.total_service = total_days
                resignation.total_service = f"{total_days} Days"
            else:
                resignation.total_service = 0

    @api.depends('resignation_line_ids.type')
    def _compute_is_pending_sal(self):
        """ Compute is_pending_sal based on resignation_line_ids.type """
        for resignation in self:
            resignation.is_pending_sal = any(line.type == 'pending_sal' for line in resignation.resignation_line_ids)

    @api.onchange('date_last_working')
    def _onchange_date_last_working(self):
        """ onchange, To get the employee worked days current month """
        if self.date_last_working:
            start_date = datetime(self.date_last_working.year, self.date_last_working.month, 1).date()
            end_date = self.date_last_working
            working_days = self._get_working_days(start_date, end_date)
            self.working_days = working_days

    def _get_working_days(self, start_date, end_date):
        """ To get the working days of current month """
        working_days = 0
        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() < 7:
                working_days += 1
            current_date += timedelta(days=1)
        return working_days

    def action_compute(self):
        """ button compute, To set the employee's pending salary based on worked days """
        for resignation in self:
            for line in resignation.resignation_line_ids:
                if line.type == 'pending_sal':
                    amount = self.contract_id.total_sal * 12 * int(self.working_days) / 365
                    line.amount = amount

    # @api.onchange('employee_id')
    # @api.constrains('employee_id')
    # def onchange_employee(self):
    #     """ onchange, To get any pending earnings and deductions of the employee """
    #     for rec in self.e_and_d_line_ids:
    #         if self.employee_id != rec.employee_id:
    #             self.e_and_d_line_ids = False
        # deduction = self.env['hr.deduction'].search(
        #     [('employee_id', '=', self.employee_id.id), ('balance_amount', '!=', 0), ('state', 'in', ['approve'])
        #      ])
        # for d in deduction:
        #     for i in d.deduction_lines:
        #         if i.state == 'active' or i.state == 'paid':
        #             if d.contract_id and d.type == 'deductions' and d.deduction_rule_id and d.deduction_rule_id.active:
        #                 ded = self.env['hr.payslip.input.type'].search([('name', '=', 'Deduction')])
        #                 val = {'name': d.deduction_rule_id.name or '',
        #                        'code': d.deduction_rule_id.code or '',
        #                        'input_type_id': ded.id,
        #                        'employee_id': d.employee_id.id,
        #                        'amount': i.amount,
        #                        # 'contract_id': d.contract_id.id,
        #                        'balance': d.balance_amount,
        #                        'salary_rule_id': d.deduction_rule_id.id,
        #                        'e_and_d_line_id': i.id,
        #                        }
        #                 self.write({'e_and_d_line_ids': [(0, 0, val)]})
        #             elif d.contract_id and d.type == 'earnings' and d.allowance_rule_id and d.allowance_rule_id.active:
        #                 earning = self.env['hr.payslip.input.type'].search([('name', '=', 'Reimbursement')])
        #                 val = {'name': d.allowance_rule_id.name or '', 'code': d.allowance_rule_id.code or '',
        #                        'amount': i.amount,
        #                        'input_type_id': earning.id,
        #                        'employee_id': d.employee_id.id,
        #                        'salary_rule_id': d.allowance_rule_id.id,
        #                        # 'contract_id': d.contract_id.id,
        #                        'balance': d.balance_amount,
        #                        'e_and_d_line_id': i.id, }
        #                 self.write({'e_and_d_line_ids': [(0, 0, val)]})

    @api.depends('employee_id', 'date_last_working')
    def _compute_payable(self):
        """ compute, To compute the pending salary and annual leave pay """
        self.pending_salary = 0
        self.annual_leave_pay = 0
        if self.working_days:
            sal_per_day = self.employee_id.contract_id.ctc_month / 30
            one_hr_ot = ((self.employee_id.contract_id.wage / 30) / 9) * 1.25
            self.pending_salary = float(self.working_days) * sal_per_day + one_hr_ot * self.total_payable_ot_hours

        if self.pending_leave_sal_days:
            leave_sal_per_day = self.employee_id.contract_id.wage + self.employee_id.contract_id.housing_allowance / 30
            self.annual_leave_pay = self.pending_leave_sal_days * leave_sal_per_day

    @api.depends('total_service')
    def _compute_calculate_gratuity(self):
        """ compute, gratuity amount calculation """
        for resignation in self:
            resignation.gratuity_amount = 0.0
            if resignation.total_service and resignation.employee_id and resignation.employee_id.contract_id:
                match = re.match(r'(\d+)', resignation.total_service)
                if match:
                    total_service_days = int(match.group(1))
                    per_day_gratuity = resignation.employee_id.contract_id.wage / 365.25
                    resignation.gratuity_amount = per_day_gratuity * total_service_days

    def action_print_pdf(self):
        """ Action button to print the PDF report of employee Gratuity """
        return self.env.ref('kg_final_settlement.action_report_employee_gratuity_id').report_action(self)


class HRResignationLines(models.Model):
    """ Employee Resignation Lines """
    _name = 'hr.resignation.line'
    _description = 'hr.resignation.line'

    resignation_id = fields.Many2one('hr.resignation')
    description = fields.Char(string='Description')
    type = fields.Selection(
        [('leave_sal', 'Leave salary'), ('pending_off', 'Pending Off'), ('pending_sal', 'Pending Salary')],
        string='Type')
    amount = fields.Float(string='Amount')


class HREarnDeductLine(models.Model):
    """ Earnings and Deduction Lines """
    _name = 'hr.earn.deduct.line'
    _description = 'hr.earn.deduct.line'

    name = fields.Char(string="Description")
    code = fields.Char(string="Code")
    resignation_id = fields.Many2one('hr.resignation')
    input_type_id = fields.Many2one('hr.payslip.input.type', string="Type")
    employee_id = fields.Many2one('hr.employee', string="Employee")
    amount = fields.Float(string="Amount")
    balance = fields.Float(string="Balance")
    salary_rule_id = fields.Many2one('hr.salary.rule', string="Salary Rule")
    e_and_d_line_id = fields.Many2one('hr.deduction.line', string="E & D")
