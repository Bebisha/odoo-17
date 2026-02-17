# -*- coding: utf-8 -*-
from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class HrEarningsDeduction(models.Model):
    _name = 'hr.earn.ded'
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
        result = super(HrEarningsDeduction, self).default_get(field_list)
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
    type = fields.Selection([('earnings', 'Earnings'), ('deductions', 'Deductions')], 'Type', default='deductions', )

    department_id = fields.Many2one('hr.department', related="employee_id.department_id", readonly=True,
                                    string="Department")
    installment = fields.Integer(string="No Of Installments", default=1)
    payment_date = fields.Date(string="Payment Start Date", required=True, default=datetime.now())
    deduction_lines = fields.One2many('hr.earn.ded.line', 'deduction_id', string="Deduction Line", index=True)

    company_id = fields.Many2one('res.company', 'Company', readonly=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    job_position = fields.Many2one('hr.job', related="employee_id.job_id", readonly=True, string="Job Position")
    deduction_amount = fields.Float(string="Amount", required=True)
    total_amount = fields.Float(string="Total Amount", readonly=True, compute='_compute_deduction_amount', store=True)
    balance_amount = fields.Float(string="Balance Amount", compute='_compute_deduction_amount', store=True)
    total_paid_amount = fields.Float(string="Total Paid Amount", compute='_compute_deduction_amount', store=True)
    is_recurring = fields.Boolean(string='Recurring')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('validate', 'Validated'),
        ('approve', 'Approved'),
        ('refuse', 'Refused'),
        ('cancel', 'Canceled'),
    ], string="State", default='draft', track_visibility='onchange', copy=False, )
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

    @api.depends('state', 'type')
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
        res = super(HrEarningsDeduction, self).create(values)
        return res

    def action_validate(self):
        """ Validating the Earnings and Deduction """
        for rec in self:
            rec.write({'state': 'validate'})

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_approve(self):
        for data in self:
            if not data.is_recurring:
                if not data.deduction_lines:
                    raise ValidationError(_("Please Compute installment"))
            data.write({'state': 'approve'})

    # def approval_check(self):
    #     active_id = self.env.context.get('active_id') if self.env.context.get(
    #         'active_id') else self.id
    #
    #     deduction = self.env['hr.deduction'].search([('id', '=', active_id)], limit=1)
    #
    #     for user_obj in deduction.deduction_approvals:
    #         if not user_obj.validation_status:
    #             approval_flag = False
    #     if approval_flag:
    #         deduction.write({'state': 'approve'})
    #         return True
    #     else:
    #         return False

    def action_refuse(self):
        return self.write({'state': 'refuse'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def unlink(self):
        for deduction in self:
            if deduction.state not in ('draft', 'cancel'):
                raise UserError(
                    'You cannot delete a deduction which is not in draft or cancelled state')
        return super(HrEarningsDeduction, self).unlink()

    def compute_installment(self):

        """This automatically create the installment the employee need to pay to
        company based on payment start date and the no of installments.
            """
        for deduction in self:
            deduction.deduction_lines.unlink()
            date_start = datetime.strptime(str(deduction.payment_date), '%Y-%m-%d')
            amount = deduction.deduction_amount / deduction.installment
            for i in range(1, deduction.installment + 1):
                self.env['hr.earn.ded.line'].create({
                    'date': date_start,
                    'amount': amount,
                    'employee_id': deduction.employee_id.id,
                    'deduction_id': deduction.id})
                date_start = date_start + relativedelta(months=1)
        return True


class InstallmentLine(models.Model):
    _name = "hr.earn.ded.line"
    _description = "Installment Line"

    date = fields.Date(string="Payment Date", required=True)
    employee_id = fields.Many2one('hr.employee', string="Employee")
    amount = fields.Float(string="Amount", required=True)
    paid = fields.Boolean(string="Paid")
    deduction_id = fields.Many2one('hr.earn.ded', string="Deduction Ref.")
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
        news_installment = self.env['hr.earn.ded.line'].create({
            'date': next_installment_date,
            'amount': self.amount,
            'employee_id': self.employee_id.id,
            'deduction_id': self.deduction_id.id,
            'state': 'active'})
        self.write({'state': 'skip'})
