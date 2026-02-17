# -*- coding: utf-8 -*-
from collections import defaultdict

import babel
from datetime import date, datetime, time, timedelta
from dateutil.relativedelta import relativedelta
from pytz import timezone, utc

from odoo import api, fields, models, tools, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
import string
from calendar import monthrange
import re

from odoo.tools import float_utils, html2plaintext, is_html_empty

ROUNDING_FACTOR = 16


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    is_earn_deduct = fields.Boolean(string="Earnings and Deduction")
    gratuity_next_month = fields.Boolean(string="Balance Payment (gratuity)")
    input_ids = fields.One2many('hr.rule.input', 'input_id', string='Inputs', copy=True)


class HrRuleInput(models.Model):
    _name = 'hr.rule.input'
    _description = 'Salary Rule Input'

    input_id = fields.Many2one('hr.salary.rule', string='Salary Rule Input', required=True)


class HrPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'
    _description = 'Payslip Input'

    balance = fields.Float(string="Balance")
    code = fields.Char(related='input_type_id.code', required=True,
                       help="The code that can be used in the salary rules")
    salary_rule_id = fields.Many2one("hr.salary.rule", string="Salary Rule")
    e_and_d_line_id = fields.Many2one("hr.deduction.line", string="E & D")


class Hrdeduction(models.Model):
    _name = 'hr.deduction'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    _description = "Earnings and Deduction Management"

    def name_get(self):
        result = []
        for rec in self:
            if rec.type == 'earnings':
                name = rec.employee_id.name + ': ' + rec.payment_date.strftime(
                    '%B') + ' - ' + rec.payment_date.strftime('%Y') + ' [' + rec.allowance_rule_id.name + '] '
            else:
                name = rec.employee_id.name + ':' + rec.payment_date.strftime('%B') + ' - ' + rec.payment_date.strftime(
                    '%Y') + ' [' + rec.deduction_rule_id.name + '] '

            result.append((rec.id, name))
        return result

    @api.model
    def default_get(self, field_list):
        result = super(Hrdeduction, self).default_get(field_list)
        if result.get('user_id'):
            ts_user_id = result['user_id']
        else:
            ts_user_id = self.env.context.get('user_id', self.env.user.id)
            result['employee_id'] = self.env['hr.employee'].search([('user_id', '=', ts_user_id)], limit=1).id
        return result

    @api.depends('deduction_lines.amount', 'deduction_lines.paid')
    def _compute_deduction_amount(self):
        for deduction in self:
            total_paid = sum(line.amount for line in deduction.deduction_lines if line.paid)
            balance_amount = deduction.deduction_amount - total_paid
            deduction.total_amount = deduction.deduction_amount
            deduction.balance_amount = balance_amount
            deduction.total_paid_amount = total_paid

    name = fields.Char(string="Reference", default="New", readonly=True)
    date = fields.Date(string="Date", default=datetime.now(), readonly=True)

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, store=True)
    contract_id = fields.Many2one('hr.contract', string="Contract", required=True)
    deduction_rule_id = fields.Many2one('hr.salary.rule', string="Deduction",
                                        domain=[('category_id.code', '=', 'DED'), ('is_earn_deduct', '=', True)],
                                        store=True)
    allowance_rule_id = fields.Many2one('hr.salary.rule', string="Allowance",
                                        domain=[('category_id.code', '=', 'ALW'), ('is_earn_deduct', '=', True)],
                                        store=True)
    deduction = fields.Selection([('traffic_violation', 'Traffic Violation'),
                                  ('insurance_deduction', 'Insurance Deduction'),
                                  ('food_deduction', 'Food Deduction'),
                                  ('car_accident_deduction', 'Car Accident Deduction'),
                                  ('family_visa_deduction', 'Family Visa Deduction'),
                                  ('ticket_deduction', 'Ticket Deduction'),
                                  ('safety_violation', 'Safety Violation'),
                                  ('warning_deduction', 'Warning Deduction'),
                                  ('accomodation_deduction', 'Accomodation Deduction'),
                                  ('arrears_deduction', 'Arrears Deduction')])

    earnings = fields.Selection([('telephone_allowance', 'Telephone Allowance'),
                                 ('air_ticket_reimbusment', 'Air Ticket Reimbusment'),
                                 ('bonus_paid', 'Bonus Paid'),
                                 ('esob_paid', 'ESOB Paid'), ])

    type = fields.Selection([('earnings', 'Earnings'), ('deductions', 'Deductions')], 'Type', default='deductions', )
    # emp_no = fields.Char(string="Emp.No", related='employee_id.emp_id', store=True)

    department_id = fields.Many2one('hr.department', related="employee_id.department_id", readonly=True,
                                    string="Department")
    installment = fields.Integer(string="No Of Installments", default=1)
    payment_date = fields.Date(string="Payment Start Date", required=True, default=datetime.now())
    deduction_lines = fields.One2many('hr.deduction.line', 'deduction_id', string="Deduction Line", index=True)

    company_id = fields.Many2one('res.company', 'Company', readonly=True,

                                 )
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    job_position = fields.Many2one('hr.job', related="employee_id.job_id", readonly=True, string="Job Position")
    deduction_amount = fields.Float(string="Amount", required=True)
    total_amount = fields.Float(string="Total Amount", readonly=True, compute='_compute_deduction_amount', store=True)
    balance_amount = fields.Float(string="Balance Amount", compute='_compute_deduction_amount', store=True)
    total_paid_amount = fields.Float(string="Total Paid Amount", compute='_compute_deduction_amount', store=True)
    normal_ot_hours = fields.Float(string="Normal OT Hours")
    public_ot_hours = fields.Float(string="Public OT Hours")
    friday_ot_hours = fields.Float(string="Off Day OT Hours")
    normal_ot_amount = fields.Float(string="Normal OT Amount")
    public_ot_amount = fields.Float(string="Public OT Amount")
    friday_ot_amount = fields.Float(string="Off Day OT Amount")
    check_rule = fields.Boolean()
    leave_encashment = fields.Boolean(string="Leave Encashment")
    leave_balance = fields.Float(string="Leave Balance")
    leave_balance_to_use = fields.Float(string="No of leaves to encash")
    is_recurring = fields.Boolean(string='Recurring')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('validate', 'Validated'),
        ('approve', 'Approved'),
        ('refuse', 'Refused'),
        ('cancel', 'Canceled'),
    ], string="State", default='draft', track_visibility='onchange', copy=False, )

    deduction_approvals = fields.One2many('deduction.approval.status',
                                          'deduction_status',
                                          string='Approval Validators',
                                          track_visibility='always',
                                          help="Approval Validators", save=True)
    super_approval_previllege = fields.Boolean('Super Approval')

    @api.onchange('super_approval_previllege')
    def check_super_approval(self):
        for rec in self:
            for user_obj in rec.deduction_approvals:

                if rec.super_approval_previllege:
                    user_obj.sudo().write({'validation_status': True})
                else:
                    user_obj.sudo().write({'validation_status': False})

    multi_level_validation = fields.Boolean(
        string='Multiple Level Approval', default=True,
        help="If checked then multi-level approval is necessary")
    approval_by = fields.Selection(
        [('coach', 'Hr Executive'), ('manager', 'Manager'), ('hr_dept', 'HR Dept'),
         ('timeoff_officer', 'Time Off Officers'), ('general_manager', 'General Manager'),
         ('hod', 'Head of Department')], string='Approval By', default='hod')

    @api.onchange('allowance_rule_id', 'type', 'deduction_rule_id', 'employee_id')
    def onchange_allowance_encahment(self):
        for rec in self:
            if rec.allowance_rule_id and rec.employee_id:
                if rec.allowance_rule_id.code == 'LEN':
                    rec.leave_encashment = True
                    annual_leave_id = self.env['hr.leave.type'].search(
                        [('code', '=', 'AL'), ('company_id', '=', rec.employee_id.company_id.id)])
                    if not annual_leave_id:
                        raise UserError("Annual Leave not found for employee")
                    mapped_days = annual_leave_id.get_employees_days([rec.employee_id.id])
                    leave_days = mapped_days[rec.employee_id.id][annual_leave_id.id]
                    balance_leave = leave_days.get('remaining_leaves')
                    rec.leave_balance = balance_leave
                else:
                    rec.leave_encashment = False

    def calculate_actual_ot_hours(self, hours):
        import math
        frac, whole = math.modf(hours)
        if frac >= .5:
            whole = whole + .5
        return whole

    def calculate_overtime_amount(self):
        """calculate normal overtime and public overtime from hours entered"""
        for rec in self:
            normal_ot_amount = 0
            public_ot_amount = 0
            if rec.employee_id.emp_type != 'labour':
                raise ValidationError(_("Overtime calculation Only for Labours !"))
            month_days = monthrange(rec.payment_date.year, rec.payment_date.month)[1]
            if rec.normal_ot_hours >= 1:
                normal_ot_hours = rec.calculate_actual_ot_hours(rec.normal_ot_hours)
                normal_ot_amount = rec.employee_id.contract_id.wage / month_days / 8 * normal_ot_hours * 1.25
            if rec.public_ot_hours >= 1:
                public_ot_hours = rec.calculate_actual_ot_hours(rec.public_ot_hours)
                public_ot_amount = rec.employee_id.contract_id.wage / month_days / 8 * public_ot_hours * 1.50
            rec.public_ot_amount = public_ot_amount
            rec.normal_ot_amount = normal_ot_amount
            return normal_ot_amount + public_ot_amount

    @api.onchange('employee_id')
    def change_employee(self):
        self.contract_id = self.employee_id.contract_id.id
        if self.allowance_rule_id:
            self.allowance_rule_id = False
        if self.deduction_rule_id:
            self.deduction_rule_id = False

    @api.onchange('deduction_rule_id', 'allowance_rule_id', 'employee_id')
    def employee_ids_earnings_deductions(self):
        if self.employee_id:
            return {'domain': {
                'deduction_rule_id': [('category_id.code', '=', 'DED'), ('is_earn_deduct', '=', True),
                                      # ('company_id', '=', self.employee_id.company_id.id)
                                      ],
                'allowance_rule_id': [('category_id.code', '=', 'ALW'), ('is_earn_deduct', '=', True),
                                      # ('company_id', '=', self.employee_id.company_id.id)
                                      ]
            }}
        else:
            return {'domain': {
                'deduction_rule_id': [('active', '=', False), ('category_id.code', '=', 'DED'),
                                      ('is_earn_deduct', '=', True),
                                      ],
                'allowance_rule_id': [('active', '=', False), ('category_id.code', '=', 'ALW'),
                                      ('is_earn_deduct', '=', True),
                                      ]
            }}

    @api.model
    def create(self, values):
        values['name'] = self.env['ir.sequence'].get('hr.deduction.seq') or ' '
        res = super(Hrdeduction, self).create(values)
        return res

    def action_validate(self):
        for rec in self:
            for approvers in rec.deduction_approvals.validating_users:
                rec.sudo().activity_schedule(
                    'deduction_management.mail_earning_deduction_record_activity',
                    user_id=approvers.id)
        self.write({'state': 'validate'})

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_approve(self):
        for data in self:
            if not data.is_recurring:
                if not data.deduction_lines:
                    raise ValidationError(_("Please Compute installment"))
            # else:
            #     self.write({'state': 'approve'})
        return self.approval_check()

    def approval_check(self):
        active_id = self.env.context.get('active_id') if self.env.context.get(
            'active_id') else self.id

        deduction = self.env['hr.deduction'].search([('id', '=', active_id)], limit=1)

        for ded in deduction:

            validation_obj = ded.deduction_approvals.search(
                [('deduction_status', '=', ded.id),
                 ('validating_users', '=', self.env.uid)])

            for v in validation_obj:
                not_approved_users = ded.deduction_approvals.search(
                    [('deduction_status', '=', ded.id),
                     ('validating_users', '!=', self.env.uid), ('validation_status', '=', False)])
                for users in not_approved_users:
                    if v.sequence > users.sequence:
                        raise ValidationError(
                            _('Deduction can be approved only when other approvers have Validated the leave request '))
                if v.validation_status != True:
                    v.validation_status = True if validation_obj else False
                    if len(not_approved_users) != 0:
                        return {
                            'effect': {
                                'type': 'rainbow_man',
                                'message': 'Approved',
                                'fadeout': 'slow',
                            }
                        }

        approval_flag = True
        for user_obj in deduction.deduction_approvals:
            if not user_obj.validation_status:
                approval_flag = False
        if approval_flag:
            deduction.write({'state': 'approve'})
            return True
        else:
            return False

    # def compute_earning_rule(self):
    #     for rec in self:
    #         if rec.deduction_rule_id:
    #             ded_rule=rec.deduction_rule_id
    #             rec.deduction_rule_id=False
    #             rec.write({'deduction_rule_id':ded_rule,'employee_id':rec.employee_id.id})
    #             rec.add_validators()
    #         if rec.allowance_rule_id:
    #             rec.write({'allowance_rule_id':rec.allowance_rule_id,'employee_id':rec.employee_id.id})
    @api.onchange('employee_id', 'deduction_rule_id', 'allowance_rule_id', 'type')
    def add_validators(self):
        """ Update the tree view and add new validators
        when leave type is changed in leave request form """
        li = []
        for rec in self:
            if rec.employee_id and (rec.deduction_rule_id or rec.allowance_rule_id):
                earnings_rec = self.env['deduction.approval.settings'].search(
                    ['|', ('deduction_rule_id', '=', rec.deduction_rule_id.id),
                     ('deduction_rule_id', '=', rec.allowance_rule_id.id), ('multi_level_validation', '=', True)])
                if earnings_rec:
                    rec.deduction_approvals = [(5, 0, 0)]
                    for user in earnings_rec.leave_validators:
                        if user.approval_by == 'timeoff_officer':
                            li.append((0, 0, {
                                'validating_users': user.sudo().holiday_validators.id,
                                'sequence': user.sequence,
                                'approval_by': user.approval_by,
                            }))
                        if user.approval_by == 'coach':
                            li.append((0, 0, {
                                'validating_users': rec.sudo().employee_id.coach_id.user_id.id,
                                'sequence': user.sequence,
                                'approval_by': user.approval_by,
                            }))
                        if user.approval_by == 'manager':
                            li.append((0, 0, {
                                'validating_users': rec.sudo().employee_id.parent_id.user_id.id,
                                'sequence': user.sequence,
                                'approval_by': user.approval_by,
                            }))
                        if user.approval_by == 'hod':
                            if rec.sudo().employee_id.parent_id:
                                li.append((0, 0, {
                                    'validating_users': rec.sudo().employee_id.parent_id.user_id.id,
                                    'sequence': user.sequence,
                                    'approval_by': user.approval_by,
                                }))
                            else:
                                li.append((0, 0, {
                                    'validating_users': rec.sudo().employee_id.department_id.manager_id.user_id.id,
                                    'sequence': user.sequence,
                                    'approval_by': user.approval_by,
                                }))
                        if user.approval_by == 'hr_dept':
                            li.append((0, 0, {
                                'validating_users': rec.sudo().employee_id.hr_dept_user_id.id,
                                'sequence': user.sequence,
                                'approval_by': user.approval_by,
                            }))
                        if user.approval_by == 'general_manager':
                            if rec.sudo().employee_id.emp_type == 'staff':
                                li.append((0, 0, {
                                    'validating_users': rec.sudo().employee_id.general_manager_id.user_id.id,
                                    'sequence': user.sequence,
                                    'approval_by': user.approval_by,
                                }))

                    rec.deduction_approvals = li


                else:
                    #
                    rec.deduction_approvals = False

    def action_refuse(self):
        return self.write({'state': 'refuse'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def unlink(self):
        for deduction in self:
            if deduction.state not in ('draft', 'cancel'):
                raise UserError(
                    'You cannot delete a deduction which is not in draft or cancelled state')
        return super(Hrdeduction, self).unlink()

    def calculate_les_amount(self):
        encashed_amount = 0
        if self.leave_encashment and self.employee_id:
            if self.leave_balance_to_use > self.leave_balance:
                raise UserError("Encashment Days entered is greater than available balance")
            else:
                encashed_amount = (self.employee_id.contract_id.monthly / 31) * self.leave_balance_to_use
                return encashed_amount
        return encashed_amount

    def compute_installment(self):

        """This automatically create the installment the employee need to pay to
        company based on payment start date and the no of installments.
            """
        for deduction in self:
            if (
                    self.normal_ot_hours != 0 or self.public_ot_hours != 0 or self.friday_ot_hours != 0) and self.allowance_rule_id.code == 'OVR':
                deduction.deduction_amount = self.calculate_overtime_amount()
            if self.leave_encashment:
                deduction.deduction_amount = self.calculate_les_amount()
            deduction.deduction_lines.unlink()
            date_start = datetime.strptime(str(deduction.payment_date), '%Y-%m-%d')
            amount = deduction.deduction_amount / deduction.installment
            for i in range(1, deduction.installment + 1):
                self.env['hr.deduction.line'].create({
                    'date': date_start,
                    'amount': amount,
                    'employee_id': deduction.employee_id.id,
                    'deduction_id': deduction.id})
                date_start = date_start + relativedelta(months=1)
        return True

    readonly_employee_id = fields.Boolean(compute='_compute_field_states')
    readonly_contract_id = fields.Boolean(compute='_compute_field_states')
    readonly_type = fields.Boolean(compute='_compute_field_states')
    readonly_deduction_rule_id = fields.Boolean(compute='_compute_field_states')
    readonly_allowance_rule_id = fields.Boolean(compute='_compute_field_states')
    readonly_deduction_amount = fields.Boolean(compute='_compute_field_states')
    readonly_installment = fields.Boolean(compute='_compute_field_states')
    readonly_payment_date = fields.Boolean(compute='_compute_field_states')

    invisible_deduction_rule_id = fields.Boolean(compute='_compute_field_states')
    invisible_allowance_rule_id = fields.Boolean(compute='_compute_field_states')

    required_deduction_rule_id = fields.Boolean(compute='_compute_field_states')
    required_allowance_rule_id = fields.Boolean(compute='_compute_field_states')

    invisible_multi_level_validation = fields.Boolean(compute='_compute_field_states')

    @api.depends('state', 'type', 'multi_level_validation')
    def _compute_field_states(self):
        for record in self:
            is_approve = record.state == 'approve'
            is_draft = record.state == 'draft'
            is_earnings = record.type == 'earnings'
            is_deductions = record.type == 'deductions'

            record.readonly_employee_id = is_approve
            record.readonly_contract_id = is_approve
            record.readonly_type = not is_draft
            record.readonly_deduction_rule_id = is_approve
            record.readonly_allowance_rule_id = is_approve
            record.readonly_deduction_amount = is_approve
            record.readonly_installment = is_approve
            record.readonly_payment_date = is_approve

            record.invisible_deduction_rule_id = is_earnings
            record.invisible_allowance_rule_id = is_earnings

            record.required_deduction_rule_id = is_deductions
            record.required_allowance_rule_id = is_deductions

            record.invisible_multi_level_validation = not record.multi_level_validation


class InstallmentLine(models.Model):
    _name = "hr.deduction.line"
    _description = "Installment Line"

    date = fields.Date(string="Payment Date", required=True)
    employee_id = fields.Many2one('hr.employee', string="Employee")
    amount = fields.Float(string="Amount", required=True)
    paid = fields.Boolean(string="Paid")
    deduction_id = fields.Many2one('hr.deduction', string="Deduction Ref.")
    payslip_id = fields.Many2one('hr.payslip', string="Payslip Ref.")
    state = fields.Selection([

        ('active', 'Active'),
        ('skip', 'Skip'), ('paid', 'Paid')

    ], string="State", default='active', track_visibility='onchange', copy=False, )

    def action_skip(self):
        installment_date = []
        for deductions in self.deduction_id.deduction_lines:
            installment_date.append(deductions.date)
        next_installment_date = max(installment_date) + relativedelta(months=1)
        news_installment = self.env['hr.deduction.line'].create({
            'date': next_installment_date,
            'amount': self.amount,
            'employee_id': self.employee_id.id,
            'deduction_id': self.deduction_id.id,
            'state': 'active'})
        self.write({'state': 'skip'})


# class HrPayslipDeduction(models.Model):
#     _inherit = 'hr.payslip'

    # def _get_payslip_lines(self):
    #     line_vals = []
    #     for payslip in self:
    #         if not payslip.contract_id:
    #             raise UserError(
    #                 _("There's no contract set on payslip %s for %s. Check that there is at least a contract set on the employee form.",
    #                   payslip.name, payslip.employee_id.name))
    #
    #         localdict = self.env.context.get('force_payslip_localdict', None)
    #         if localdict is None:
    #             localdict = payslip._get_localdict()
    #
    #         rules_dict = localdict['rules']
    #         result_rules_dict = localdict['result_rules']
    #
    #         blacklisted_rule_ids = self.env.context.get('prevent_payslip_computation_line_ids', [])
    #
    #         result = {}
    #         for rule in sorted(payslip.struct_id.rule_ids, key=lambda x: x.sequence):
    #             if rule.id in blacklisted_rule_ids:
    #                 continue
    #             localdict.update({
    #                 'result': None,
    #                 'result_qty': 1.0,
    #                 'result_rate': 100,
    #                 'result_name': False
    #             })
    #             if rule._satisfy_condition(localdict):
    #                 # Retrieve the line name in the employee's lang
    #                 employee_lang = payslip.employee_id.lang
    #                 # This actually has an impact, don't remove this line
    #                 context = {'lang': employee_lang}
    #                 if rule.code in localdict['same_type_input_lines']:
    #                     for multi_line_rule in localdict['same_type_input_lines'][rule.code]:
    #                         if 'inputs' not in localdict:
    #                             localdict['inputs'] = {}
    #
    #                         localdict['inputs'][rule.code] = multi_line_rule
    #                         # localdict['inputs'].dict[rule.code] = multi_line_rule
    #                         amount, qty, rate = rule._compute_rule(localdict)
    #                         tot_rule = amount * qty * rate / 100.0
    #                         localdict = rule.category_id._sum_salary_rule_category(localdict,
    #                                                                                tot_rule)
    #                         rule_name = payslip._get_rule_name(localdict, rule, employee_lang)
    #                         line_vals.append({
    #                             'sequence': rule.sequence,
    #                             'code': rule.code,
    #                             'name': rule_name,
    #                             'salary_rule_id': rule.id,
    #                             'contract_id': localdict['contract'].id,
    #                             'employee_id': localdict['employee'].id,
    #                             'amount': amount,
    #                             'quantity': qty,
    #                             'rate': rate,
    #                             'slip_id': payslip.id,
    #                         })
    #                 else:
    #                     amount, qty, rate = rule._compute_rule(localdict)
    #                     # check if there is already a rule computed with that code
    #                     previous_amount = localdict.get(rule.code, 0.0)
    #                     # set/overwrite the amount computed for this rule in the localdict
    #                     tot_rule = amount * qty * rate / 100.0
    #                     localdict[rule.code] = tot_rule
    #                     result_rules_dict[rule.code] = {'total': tot_rule, 'amount': amount, 'quantity': qty,
    #                                                     'rate': rate}
    #                     rules_dict[rule.code] = rule
    #                     # sum the amount for its salary category
    #                     localdict = rule.category_id._sum_salary_rule_category(localdict, tot_rule - previous_amount)
    #                     rule_name = payslip._get_rule_name(localdict, rule, employee_lang)
    #                     # create/overwrite the rule in the temporary results
    #                     result[rule.code] = {
    #                         'sequence': rule.sequence,
    #                         'code': rule.code,
    #                         'name': rule_name,
    #                         'salary_rule_id': rule.id,
    #                         'contract_id': localdict['contract'].id,
    #                         'employee_id': localdict['employee'].id,
    #                         'amount': amount,
    #                         'quantity': qty,
    #                         'rate': rate,
    #                         'slip_id': payslip.id,
    #                     }
    #         line_vals += list(result.values())
    #     return line_vals

    # def _get_payslip_lines(self):
    #     line_vals = []
    #     for payslip in self:
    #         if not payslip.contract_id:
    #             raise UserError(
    #                 _("There's no contract set on payslip %s for %s. Check that there is at least a contract set on the employee form.",
    #                   payslip.name, payslip.employee_id.name))
    #
    #         localdict = self.env.context.get('force_payslip_localdict', None)
    #         if localdict is None:
    #             localdict = payslip._get_localdict()
    #
    #         # rules_dict = localdict['rules'].dict
    #         # result_rules_dict = localdict['result_rules'].dict
    #
    #         blacklisted_rule_ids = self.env.context.get('prevent_payslip_computation_line_ids', [])
    #
    #         result = {}
    #         for rule in sorted(payslip.struct_id.rule_ids, key=lambda x: x.sequence):
    #             if rule.id in blacklisted_rule_ids:
    #                 continue
    #             localdict.update({
    #                 'result': None,
    #                 'result_qty': 1.0,
    #                 'result_rate': 100,
    #                 'result_name': False
    #             })
    #             if rule._satisfy_condition(localdict):
    #                 amount, qty, rate = rule._compute_rule(localdict)
    #                 # check if there is already a rule computed with that code
    #                 previous_amount = rule.code in localdict and localdict[rule.code] or 0.0
    #                 # set/overwrite the amount computed for this rule in the localdict
    #                 tot_rule = amount * qty * rate / 100.0
    #                 localdict[rule.code] = tot_rule
    #                 result_rules_dict[rule.code] = {'total': tot_rule, 'amount': amount, 'quantity': qty}
    #                 rules_dict[rule.code] = rule
    #                 # sum the amount for its salary category
    #                 localdict = rule.category_id._sum_salary_rule_category(localdict, tot_rule - previous_amount)
    #                 # Retrieve the line name in the employee's lang
    #                 employee_lang = payslip.employee_id.sudo().address_home_id.lang
    #                 # This actually has an impact, don't remove this line
    #                 context = {'lang': employee_lang}
    #                 if localdict['result_name']:
    #                     rule_name = localdict['result_name']
    #                 elif rule.code in ['BASIC', 'GROSS', 'NET', 'DEDUCTION',
    #                                    'REIMBURSEMENT']:  # Generated by default_get (no xmlid)
    #                     if rule.code == 'BASIC':  # Note: Crappy way to code this, but _(foo) is forbidden. Make a method in master to be overridden, using the structure code
    #                         if rule.name == "Double Holiday Pay":
    #                             rule_name = _("Double Holiday Pay")
    #                         if rule.struct_id.name == "CP200: Employees 13th Month":
    #                             rule_name = _("Prorated end-of-year bonus")
    #                         else:
    #                             rule_name = _('Basic Salary')
    #                     elif rule.code == "GROSS":
    #                         rule_name = _('Gross')
    #                     elif rule.code == "DEDUCTION":
    #                         rule_name = _('Deduction')
    #                     elif rule.code == "REIMBURSEMENT":
    #                         rule_name = _('Reimbursement')
    #                     elif rule.code == 'NET':
    #                         rule_name = _('Net Salary')
    #                 else:
    #                     rule_name = rule.with_context(lang=employee_lang).name
    #                 # create/overwrite the rule in the temporary results
    #                 # if not rule.is_earn_deduct:
    #                 result[rule.code] = {
    #                     'sequence': rule.sequence,
    #                     'code': rule.code,
    #                     'name': rule_name,
    #                     'note': html2plaintext(rule.note) if not is_html_empty(rule.note) else '',
    #                     'salary_rule_id': rule.id,
    #                     'contract_id': localdict['contract'].id,
    #                     'employee_id': localdict['employee'].id,
    #                     'amount': amount,
    #                     'quantity': qty,
    #                     'rate': rate,
    #                     'slip_id': payslip.id,
    #                 }
    #         line_vals += list(result.values())
    #     return line_vals

    @api.model
    def get_contract(self, employee, date_from, date_to):
        """
        @param employee: recordset of employee
        @param date_from: date field
        @param date_to: date field
        @return: returns the ids of all the contracts for the given employee that need to be considered for the given dates
        """
        # a contract is valid if it ends between the given dates
        clause_1 = ['&', ('date_end', '<=', date_to), ('date_end', '>=', date_from)]
        # OR if it starts between the given dates
        clause_2 = ['&', ('date_start', '<=', date_to), ('date_start', '>=', date_from)]
        # OR if it starts before the date_from and finish after the date_end (or never finish)
        clause_3 = ['&', ('date_start', '<=', date_from), '|', ('date_end', '=', False), ('date_end', '>=', date_to)]
        clause_final = [('employee_id', '=', employee.id), ('state', '=', 'open'), '|',
                        '|'] + clause_1 + clause_2 + clause_3
        return self.env['hr.contract'].search(clause_final).ids

    # def get_inputs(self, contracts, date_from, date_to):
    #     res = []
    #
    #     # structure_ids = contracts.get_all_structures()
    #     structure_ids = contracts.get_all_structures()
    #     rule_ids = self.env['hr.payroll.structure'].browse(structure_ids).get_all_rules()
    #     sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x: x[1])]
    #     inputs = self.env['hr.salary.rule'].browse(sorted_rule_ids).mapped('input_ids')
    #     for contract in contracts:
    #         for input in inputs:
    #             input_data = {
    #                 'name': input.name,
    #                 'code': input.code,
    #                 'contract_id': contract.id,
    #             }
    #             res += [input_data]
    #     return res

    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        """Function for getting contracts upon date_from and date_to fields"""
        res = []
        structure_ids = contracts.get_all_structures()
        rule_ids = self.env['hr.payroll.structure'].browse(
            structure_ids).get_all_rules()
        sorted_rule_ids = [id for id, sequence in
                           sorted(rule_ids, key=lambda x: x[1])]
        inputs = self.env['hr.salary.rule'].browse(sorted_rule_ids).mapped(
            'input_ids')
        for contract in contracts:
            for input in inputs:
                input_data = {
                    'name': input.name,
                    'code': input.code,
                    'contract_id': contract.id,
                    'date_from': date_from,
                    'date_to': date_to,
                    'amount': input.amount
                }
                res.append(input_data)
        return res

    def get_worked_day_lines(self, contracts, date_from, date_to):
        """
        @param contract: Browse record of contracts
        @return: returns a list of dict containing the input that should be applied for the given contract between date_from and date_to
        """
        res = []
        # fill only if the contract as a working schedule linked
        for contract in contracts.filtered(lambda contract: contract.resource_calendar_id):
            day_from = datetime.combine(fields.Date.from_string(date_from), time.min)
            day_to = datetime.combine(fields.Date.from_string(date_to), time.max)

            # compute leave days
            leaves = {}
            calendar = contract.resource_calendar_id
            tz = timezone(calendar.tz)
            day_leave_intervals = contract.employee_id.list_leaves(day_from, day_to,
                                                                   calendar=contract.resource_calendar_id)
            for day, hours, leave in day_leave_intervals:
                holiday = leave.holiday_id
                current_leave_struct = leaves.setdefault(holiday.holiday_status_id, {
                    'name': holiday.holiday_status_id.name or _('Global Leaves'),
                    'sequence': 5,
                    # 'code': holiday.holiday_status_id.code or 'GLOBAL',
                    'number_of_days': 0.0,
                    'number_of_hours': 0.0,
                    'contract_id': contract.id,
                })
                current_leave_struct['number_of_hours'] -= hours
                work_hours = calendar.get_work_hours_count(
                    tz.localize(datetime.combine(day, time.min)),
                    tz.localize(datetime.combine(day, time.max)),
                    compute_leaves=False,
                )
                if work_hours:
                    current_leave_struct['number_of_days'] -= hours / work_hours

            # compute worked days
            work_data = contract.employee_id._get_work_days_data(
                day_from,
                day_to,
                calendar=contract.resource_calendar_id,
                compute_leaves=False,
            )
            attendances_type = self.env['hr.work.entry.type'].search([('code', '=', 'WORK100')])
            attendances = {
                'work_entry_type_id': attendances_type.id,
                'name': _("Normal Working Days paid at 100%"),
                'sequence': 1,
                # 'code': 'WORK100',
                'number_of_days': work_data['days'],
                'number_of_hours': work_data['hours'],
                'contract_id': contract.id,
            }

            res.append(attendances)
            res.extend(leaves.values())
        return res

    # @api.onchange('employee_id', 'date_from', 'date_to')
    # @api.constrains('employee_id', 'date_from', 'date_to')
    # def onchange_employee(self):
    #     for record in self:
    #         if not record.employee_id or not record.date_from or not record.date_to:
    #             continue
    #
    #         employee = record.employee_id
    #         date_from = record.date_from
    #
    #         ttyme = datetime.combine(fields.Date.from_string(date_from), time.min)
    #         locale = record.env.context.get('lang') or 'en_US'
    #         record.name = _('Salary Slip of %s for %s') % (
    #             employee.name, tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale)))
    #         record.company_id = employee.company_id
    #
    #         deduction = record.env['hr.deduction'].search(
    #             [('employee_id', '=', record.employee_id.id), ('state', 'in', ['approve']),
    #              ('balance_amount', '!=', 0)])
    #         for d in deduction:
    #             total_paid = 0.0
    #             if d.is_recurring:
    #                 if d.contract_id and d.type == 'deductions' and d.deduction_rule_id and d.deduction_rule_id.active:
    #                     ded = record.env['hr.payslip.input.type'].search([('name', '=', 'Deduction')])
    #                     val = {'name': d.deduction_rule_id.name or '',
    #                            'code': d.deduction_rule_id.code or '',
    #                            'input_type_id': ded.id,
    #                            'amount': d.deduction_amount,
    #                            'contract_id': d.contract_id.id,
    #                            'salary_rule_id': d.deduction_rule_id.id,
    #                            }
    #                     record.write({'input_line_ids': [(0, 0, val)]})
    #                 elif d.contract_id and d.type == 'earnings' and d.allowance_rule_id and d.allowance_rule_id.active:
    #                     earning = record.env['hr.payslip.input.type'].search([('code', '=', 'REIMBURSEMENT')])
    #                     val = {'name': d.allowance_rule_id.name or '',
    #                            'code': d.allowance_rule_id.code or '',
    #                            'amount': d.deduction_amount,
    #                            'input_type_id': earning.id,
    #                            'salary_rule_id': d.allowance_rule_id.id,
    #                            'contract_id': d.contract_id.id,
    #                            }
    #                     record.write({'input_line_ids': [(0, 0, val)]})
    #             else:
    #                 for i in d.deduction_lines:
    #                     if i.state == 'active' or i.state == 'paid':
    #                         if i.paid:
    #                             total_paid += i.amount
    #                         if i.date <= record.date_to:
    #                             if total_paid == 0.0:
    #                                 balance_amount = d.deduction_amount - i.amount
    #                             else:
    #                                 balance_amount = d.deduction_amount - total_paid
    #                             if d.contract_id and d.type == 'deductions' and d.deduction_rule_id and d.deduction_rule_id.active:
    #                                 ded = record.env['hr.payslip.input.type'].search([('name', '=', 'Deduction')])
    #                                 val = {'name': d.deduction_rule_id.name or '',
    #                                        'code': d.deduction_rule_id.code or '',
    #                                        'input_type_id': ded.id,
    #                                        'amount': i.amount,
    #                                        'contract_id': d.contract_id.id,
    #                                        'balance': balance_amount,
    #                                        'salary_rule_id': d.deduction_rule_id.id,
    #                                        'e_and_d_line_id': i.id,
    #                                        }
    #                                 record.write({'input_line_ids': [(0, 0, val)]})
    #                             elif d.contract_id and d.type == 'earnings' and d.allowance_rule_id and d.allowance_rule_id.active:
    #                                 earning = record.env['hr.payslip.input.type'].search(
    #                                     [('code', '=', 'REIMBURSEMENT')])
    #                                 val = {'name': d.allowance_rule_id.name or '',
    #                                        'code': d.allowance_rule_id.code or '',
    #                                        'amount': i.amount,
    #                                        'input_type_id': earning.id,
    #                                        'salary_rule_id': d.allowance_rule_id.id,
    #                                        'contract_id': d.contract_id.id,
    #                                        'balance': balance_amount,
    #                                        'e_and_d_line_id': i.id, }
    #                                 record.write({'input_line_ids': [(0, 0, val)]})


# @api.onchange('employee_id', 'date_from', 'date_to')
# @api.constrains('employee_id', 'date_from', 'date_to')
# def onchange_employee(self):
#     self.ensure_one()
#     if (not self.employee_id) or (not self.date_from) or (not self.date_to):
#         return
#     employee = self.employee_id
#     date_from = self.date_from
#     date_to = self.date_to
#     contract_ids = []
#
#     ttyme = datetime.combine(fields.Date.from_string(date_from), time.min)
#     locale = self.env.context.get('lang') or 'en_US'
#     self.name = _('Salary Slip of %s for %s') % (
#         employee.name, tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale)))
#     self.company_id = employee.company_id
#
#     if not self.env.context.get('contract') or not self.contract_id:
#         contract_ids = self.get_contract(employee, date_from, date_to)
#         if not contract_ids:
#             return
#         self.contract_id = self.env['hr.contract'].browse(contract_ids[0])
#
#     # if not self.contract_id.struct_id:
#     #     return
#     # self.struct_id = self.contract_id.struct_id
#
#
#     # computation of the salary input
#     contracts = self.env['hr.contract'].browse(contract_ids)
#     if contracts:
#         # worked_days_line_ids = self.get_worked_day_lines(contracts, date_from, date_to)
#         # worked_days_lines = self.worked_days_line_ids.browse([])
#         # for r in worked_days_line_ids:
#         #     worked_days_lines += worked_days_lines.new(r)
#         # self.worked_days_line_ids = worked_days_lines
#
#         input_line_ids = self.get_inputs(contracts, date_from, date_to)
#         input_lines = self.input_line_ids.browse([])
#         for r in input_line_ids:
#             input_lines += input_lines.new(r)
#         self.input_line_ids = input_lines
#
#         deduction = self.env['hr.deduction'].search(
#             [('employee_id', '=', self.employee_id.id), ('state', 'in', ['approve'])
#              ])
#         # if self.leave_encashment and not self.include_earnings:
#         #     return True
#         # if self.gratuity_advance:
#         #     return True
#         for d in deduction:
#             total_paid = 0.0
#             if d.is_recurring:
#                 if d.contract_id and d.type == 'deductions' and d.deduction_rule_id and d.deduction_rule_id.active:
#                     ded = self.env['hr.payslip.input.type'].search([('name', '=', 'Deduction')])
#                     val = {'name': d.deduction_rule_id.name or '',
#                            'code': d.deduction_rule_id.code or '',
#                            'input_type_id': ded.id,
#                            'amount': d.deduction_amount,
#                            'contract_id': d.contract_id.id,
#                            # 'balance': balance_amount,
#                            'salary_rule_id': d.deduction_rule_id.id,
#                            # 'e_and_d_line_id': i.id,
#                            }
#                     self.write({'input_line_ids': [(0, 0, val)]})
#                 elif d.contract_id and d.type == 'earnings' and d.allowance_rule_id and d.allowance_rule_id.active:
#                     earning = self.env['hr.payslip.input.type'].search([('name', '=', 'Reimbursement')])
#                     val = {'name': d.allowance_rule_id.name or '',
#                            'code': d.allowance_rule_id.code or '',
#                            'amount': d.deduction_amount,
#                            'input_type_id': earning.id,
#                            'salary_rule_id': d.allowance_rule_id.id,
#                            'contract_id': d.contract_id.id,
#                            # 'balance': balance_amount,
#                            # 'e_and_d_line_id': i.id,
#                            }
#                     self.write({'input_line_ids': [(0, 0, val)]})
#             else:
#                 for i in d.deduction_lines:
#                     if i.state == 'active' or i.state == 'paid':
#                         if i.paid:
#                             total_paid += i.amount
#                         #     past unpaid records should also be shown
#                         if i.date <= self.date_to:
#                             if total_paid == 0.0:
#                                 balance_amount = d.deduction_amount - i.amount
#                             elif total_paid != 0.0:
#                                 balance_amount = d.deduction_amount - total_paid
#                             if d.contract_id and d.type == 'deductions' and d.deduction_rule_id and d.deduction_rule_id.active:
#                                 ded = self.env['hr.payslip.input.type'].search([('name', '=', 'Deduction')])
#                                 val = {'name': d.deduction_rule_id.name or '',
#                                        'code': d.deduction_rule_id.code or '',
#                                        'input_type_id': ded.id,
#                                        'amount': i.amount,
#                                        'contract_id': d.contract_id.id,
#                                        'balance': balance_amount,
#                                        'salary_rule_id': d.deduction_rule_id.id,
#                                        'e_and_d_line_id': i.id,
#                                        }
#                                 self.write({'input_line_ids': [(0, 0, val)]})
#                             elif d.contract_id and d.type == 'earnings' and d.allowance_rule_id and d.allowance_rule_id.active:
#                                 earning = self.env['hr.payslip.input.type'].search([('name', '=', 'Reimbursement')])
#                                 val = {'name': d.allowance_rule_id.name or '',
#                                        'code': d.allowance_rule_id.code or '',
#                                        'amount': i.amount,
#                                        'input_type_id': earning.id,
#                                        'salary_rule_id': d.allowance_rule_id.id,
#                                        'contract_id': d.contract_id.id,
#                                        'balance': balance_amount,
#                                        'e_and_d_line_id': i.id, }
#                                 self.write({'input_line_ids': [(0, 0, val)]})
#
#         return

# @api.onchange('employee_id','date_from','date_to')
# def onchange_employee_id_ded(self):
#     for record in self:
#         record.input_line_ids.unlink()
#         deduction = self.env['hr.deduction'].search(
#             [('employee_id', '=', record.employee_id.id), ('state', '=', 'validate')])
#         for d in deduction:
#             total_paid = 0.0
#             for i in d.deduction_lines:
#                 if i.state == 'active' or i.state == 'paid':
#                     if i.paid:
#                         total_paid += i.amount
#                     if i.date >= record.date_from and i.date <= record.date_to:
#                         if total_paid == 0.0:
#                             balance_amount = d.deduction_amount - i.amount
#                         elif total_paid != 0.0:
#                             balance_amount = d.deduction_amount - total_paid
#                         if d.contract_id and d.type == 'deductions' and d.deduction_rule_id:
#                             val = {'name': d.deduction_rule_id.name or '', 'code': d.deduction_rule_id.code or '',
#                                    'amount': i.amount,
#                                    'contract_id': d.contract_id.id,
#                                    'balance': balance_amount,
#                                    'salary_rule_id': d.deduction_rule_id.id,
#                                    'e_and_d_line_id': i.id,
#                                    }
#                             record.write({'input_line_ids': [(0, 0, val)]})
#                         elif d.contract_id and d.type == 'earnings' and d.allowance_rule_id:
#                             val = {'name': d.allowance_rule_id.name or '', 'code': d.allowance_rule_id.code or '',
#                                    'amount': i.amount, 'salary_rule_id': d.allowance_rule_id.id,
#                                    'contract_id': d.contract_id.id, 'balance': balance_amount,
#                                    'e_and_d_line_id': i.id,}
#                             record.write({'input_line_ids': [(0, 0, val)]})

def action_register_payment(self):
    for record in self:
        res = super(HrPayslipDeduction, record).action_register_payment()
        for inp in record.input_line_ids:
            if inp.e_and_d_line_id:
                inp.e_and_d_line_id.write({'state': 'paid',
                                           'paid': True})
        return res


class EarnDedElements(models.Model):
    _name = "earn.ded.elements"
    _description = "E&D Elements"

    name = fields.Char(string="Name")
    short_code = fields.Char('Code', copy=False)
    salary_struct_id = fields.Many2one('hr.payroll.structure', string="Structure")
    element_type = fields.Selection([('earn', 'Earnings'), ('ded', 'Deduction')])
    rule_id = fields.Many2one('hr.salary.rule', string="Rule Id", copy=False)
    active = fields.Boolean('Active')
    no_delete = fields.Boolean(default=False, string="No Delete")

    _sql_constraints = [
        ('unique_short_code', 'unique(short_code)', 'The code must be unique!'),
    ]

    @api.onchange('short_code')
    def set_caps(self):
        for rec in self:
            # rec.short_code = string.capwords(rec.short_code) if rec.short_code else False
            if rec.short_code:
                upper_case_short_code = rec.short_code.upper()
                regex = "[@!#$%^&*()[<>?/|}]{~:=,+-]."
                if any(sp in rec.short_code for sp in regex):
                    raise UserError('No Special Characters Allowed !')
                elif self.search([('short_code', '=', upper_case_short_code)], limit=1):
                    raise UserError(
                        'This code has been already assigned with an element..Please try another one !!')
                else:
                    rec.short_code = upper_case_short_code

    def apply_rule(self):
        rule_cat_domain = [('code', '=', 'DED')] if self.element_type == 'ded' else [('code', '=', 'ALW')]
        rule_cat_id = self.env['hr.salary.rule.category'].search(rule_cat_domain, limit=1)

        code = self.short_code

        # operator = '-' if self.element_type == 'ded' else '+'
        if self.element_type == 'ded':
            operator = '-inputs[\'{}\'].amount'.format(code)
        else:
            operator = 'inputs[\'{}\'].amount > 0.0'.format(code)
        # python_expression = 'result = -min(result_rules['BASIC']['total']'.format(code, operator, code)
        # python_expression = 'result = inputs.{} and {} (inputs.{}.amount)'.format(code, operator,code)
        python_code = 'result = {1} if \'{0}\' in inputs else False'.format(code, operator)

        python_expression = 'result = {1} if \'{0}\' in inputs else False'.format(code, operator)

        vals = {
            'name': self.name,
            'struct_id': self.salary_struct_id.id,
            'category_id': rule_cat_id.id,
            'code': code,
            'active': True,
            'is_earn_deduct': True,
            'amount_select': 'code',
            'condition_select': 'python',
            'condition_python': python_code,
            'amount_python_compute': python_expression
        }
        if not self.rule_id:
            salary_rule_exist = self.env['hr.salary.rule'].search([('code', '=', self.short_code)], limit=1)
            if not salary_rule_exist:
                rule_id = self.env['hr.salary.rule'].create(vals)
                self.rule_id = rule_id.id
                self.salary_struct_id.rule_ids = [(4, self.rule_id.id)]
            else:
                self.rule_id = salary_rule_exist.id
                self.salary_struct_id.rule_ids = [(4, self.rule_id.id)]
        else:
            if not self.short_code == self.rule_id.code or not self.check_rule_match():
                self.rule_id.write(vals)
            if not self.rule_id.active:
                self.rule_id.active = True
            if not self.rule_id.id in self.salary_struct_id.rule_ids.ids:
                self.salary_struct_id.rule_ids = [(4, self.rule_id.id)]
        try:
            self.active = True if not self.active else False
        except Exception as e:
            return e

    def copy(self, default=None):
        default = dict(default or {})
        default.update(name=_("%s (copy)") % self.name)
        return super().copy(default)

    def check_rule_match(self):
        if self.rule_id:
            if self.element_type == 'earn' and self.rule_id.category_id.code == 'ALW' or self.element_type == 'ded' and self.rule_id.category_id.code == 'DED':
                return True
            else:
                return False

    def disable_rule(self):
        for rec in self:
            rec.rule_id.active = False
            rec.active = False

    def action_archive(self):
        self.rule_id.active = False
        return super(EarnDedElements, self).action_archive()

    def action_unarchive(self):
        [rec.apply_rule() for rec in self]
        return super(EarnDedElements, self).action_unarchive()


    def unlink(self):
        for elem in self:
            if elem.no_delete:
                raise UserError(_("You cannot delete the element '%s'." % elem.name))
        return super(EarnDedElements, self).unlink()


class HRContract(models.Model):
    _inherit = "hr.contract"
    _description = "HR Contract"

    struct_id = fields.Many2one('hr.payroll.structure', string='Salary Structure')

    def get_all_structures(self):
        """
        @return: the structures linked to the given contracts, ordered by hierachy (parent=False first,
                 then first level children and so on) and without duplicata
        """
        pass
        # structures = self.mapped('struct_id')
        # if not structures:
        #     return []
        # # YTI TODO return browse records
        # return list(set(structures._get_parent_structure().ids))


class ResourceMixin(models.AbstractModel):
    _inherit = "resource.mixin"

    def _get_work_days_data(self, from_datetime, to_datetime, compute_leaves=True, calendar=None, domain=None):
        """
            By default the resource calendar is used, but it can be
            changed using the `calendar` argument.

            `domain` is used in order to recognise the leaves to take,
            None means default value ('time_type', '=', 'leave')

            Returns a dict {'days': n, 'hours': h} containing the
            quantity of working time expressed as days and as hours.
        """
        resource = self.resource_id
        calendar = calendar or self.resource_calendar_id

        # naive datetimes are made explicit in UTC
        if not from_datetime.tzinfo:
            from_datetime = from_datetime.replace(tzinfo=utc)
        if not to_datetime.tzinfo:
            to_datetime = to_datetime.replace(tzinfo=utc)

        # total hours per day: retrieve attendances with one extra day margin,
        # in order to compute the total hours on the first and last days
        from_full = from_datetime - timedelta(days=1)
        to_full = to_datetime + timedelta(days=1)
        intervals = calendar._attendance_intervals_batch(from_full, to_full, resource)
        day_total = defaultdict(float)
        for start, stop, meta in intervals[resource.id]:
            day_total[start.date()] += (stop - start).total_seconds() / 3600

        # actual hours per day
        if compute_leaves:
            intervals = calendar._work_intervals_batch(from_datetime, to_datetime, resource, domain)
        else:
            intervals = calendar._attendance_intervals_batch(from_datetime, to_datetime, resource)
        day_hours = defaultdict(float)
        for start, stop, meta in intervals[resource.id]:
            day_hours[start.date()] += (stop - start).total_seconds() / 3600

        # compute number of days as quarters
        days = sum(
            float_utils.round(ROUNDING_FACTOR * day_hours[day] / day_total[day]) / ROUNDING_FACTOR
            for day in day_hours
        )
        return {
            'days': days,
            'hours': sum(day_hours.values()),
        }


class HrPayrollStructure(models.Model):
    """
    Salary structure used to defined
    - Basic
    - Allowances
    - Deductions
    """
    _inherit = 'hr.payroll.structure'
    _description = 'Salary Structure'

    def get_all_rules(self):
        """
        @return: returns a list of tuple (id, sequence) of rules that are maybe to apply
        """
        all_rules = []
        for struct in self:
            all_rules += struct.rule_ids._recursive_search_of_rules()
        return all_rules
