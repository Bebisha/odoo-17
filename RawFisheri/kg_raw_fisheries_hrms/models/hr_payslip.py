# -*- coding: utf-8 -*-
from collections import defaultdict

import babel
from datetime import date, datetime, time, timedelta

from markupsafe import Markup

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import html2plaintext, is_html_empty, plaintext2html, float_compare


class HRPayslip(models.Model):
    _inherit = 'hr.payslip'
    _description = 'hr.payslip'

    partial_payment = fields.Boolean(string='Is Partial Payment?')
    payment_percent = fields.Float(string='Payment Percentage')
    settlement_date = fields.Date(string='Settlement Date',
                                  default=lambda self: datetime(datetime.today().year + 1, 3, 1))
    total_worked_days = fields.Float(string='Total Worked Days', compute='_compute_total_worked_days', store=True)
    company_currency_id = fields.Many2one('res.currency', string='Company Currency', related='company_id.currency_id')
    currency_id = fields.Many2one('res.currency', readonly=False, related='contract_id.foreign_currency_id', store=True)

    @api.depends('worked_days_line_ids')
    def _compute_total_worked_days(self):
        for payslip in self:
            payslip.total_worked_days = sum(
                payslip.worked_days_line_ids.filtered(lambda wd: wd.code != 'OUT').mapped('number_of_days')
            )

    def action_partial_payment(self):
        """ Functon to create other input for the amount to be deducted
        from salary and create a pending salary for the same """
        for rec in self:
            if rec.partial_payment:
                payment = (rec.payment_percent / 100) * rec.net_wage
                amount = rec.net_wage - payment
                ded = self.env['hr.payslip.input.type'].search([('name', '=', 'Deduction')])
                val = {
                    'name': 'Partial Salary',
                    'code': 'DEDUCTION',
                    'input_type_id': ded.id,
                    'amount': amount,
                    'contract_id': rec.employee_id.contract_id.id,
                }
                rec.write({'input_line_ids': [(0, 0, val)]})
                rec.sudo().compute_sheet()

                vals = {
                    'employee_id': rec.employee_id.id,
                    'settlement_date': rec.settlement_date,
                    'amount': amount,
                }

                self.env['pending.salary'].sudo().create(vals)

    @api.onchange('employee_id', 'date_from', 'date_to')
    def _onchange_employee_id(self):
        """ For reflecting the employee entries, salary pre-payments and delayed salaries in payslip """
        for payslip in self:
            payslip.input_line_ids = False
            employee_entries = self.env['hr.employee.entry'].search(
                [('employee_id', '=', payslip.employee_id.id), ('start_date', '>=', payslip.date_from),
                 ('end_date', '<=', payslip.date_to), ('state', '=', 'approved')])
            pre_payments = self.env['salary.pre.payment'].search(
                [('employee_id', '=', payslip.employee_id.id), ('paid_date', '>=', payslip.date_from),
                 ('paid_date', '<=', payslip.date_to), ('state', '=', 'approved')])
            pending_salaries = self.env['pending.salary'].search(
                [('employee_id', '=', payslip.employee_id.id), ('settlement_date', '>=', payslip.date_from),
                 ('settlement_date', '<=', payslip.date_to), ('state', '=', 'approved')])

            shop_deduction = sum(employee_entries.mapped('shop_deduction'))
            over_time = sum(employee_entries.mapped('over_time'))
            bonus = sum(employee_entries.mapped('bonus'))
            discharge_allowance = sum(employee_entries.mapped('discharge_qty'))
            holiday_allowance = sum(employee_entries.mapped('holiday_allowance'))
            penalty = sum(employee_entries.mapped('penalty'))
            pending_salaries = sum(pending_salaries.mapped('amount'))
            # pre_payment_deduction = sum(pre_payments.mapped('amount'))
            pre_payment_deduction = 0.0
            for pre_payment in pre_payments:
                payment_currency = pre_payment.currency_id
                amount = pre_payment.amount

                if pre_payment.currency_id != payslip.currency_id:
                    amount = payment_currency._convert(
                        amount,
                        payslip.currency_id,
                        payslip.company_id,
                        payslip.date
                    )

                pre_payment_deduction += amount
            allowance_type_id = self.env['hr.payslip.input.type'].search([('code', '=', 'REIMBURSEMENT')])
            over_time_type_id = self.env['hr.payslip.input.type'].search([('code', '=', 'OVERTIME')])
            bonus_type_id = self.env['hr.payslip.input.type'].search([('code', '=', 'EXTRAINCOME')])
            discharge_type_id = self.env['hr.payslip.input.type'].search([('code', '=', 'DISCHARGE')])
            deduction_type_id = self.env['hr.payslip.input.type'].search([('code', '=', 'DEDUCTION')])

            if over_time:
                if payslip.contract_id.foreign_currency_id and payslip.contract_id.foreign_currency_id != self.company_currency_id:
                    over_time = self.company_currency_id._convert(
                        over_time,
                        payslip.contract_id.foreign_currency_id,
                        self.env.company,
                        fields.Date.today()
                    )
                val = {
                    'name': 'Over Time',
                    'code': 'OVERTIME',
                    'input_type_id': over_time_type_id.id,
                    'amount': over_time,
                    'contract_id': payslip.employee_id.contract_id.id,
                }
                payslip.write({'input_line_ids': [(0, 0, val)]})

            if bonus:
                if payslip.contract_id.foreign_currency_id and payslip.contract_id.foreign_currency_id != self.company_currency_id:
                    bonus = self.company_currency_id._convert(
                        bonus,
                        payslip.contract_id.foreign_currency_id,
                        self.env.company,
                        fields.Date.today()
                    )
                val = {
                    'name': 'Extra Income',
                    'code': 'EXTRAINCOME',
                    'input_type_id': bonus_type_id.id,
                    'amount': bonus,
                    'contract_id': payslip.employee_id.contract_id.id,
                }
                payslip.write({'input_line_ids': [(0, 0, val)]})

            if discharge_allowance:
                if payslip.contract_id.foreign_currency_id and payslip.contract_id.foreign_currency_id != self.company_currency_id:
                    discharge_allowance = self.company_currency_id._convert(
                        discharge_allowance,
                        payslip.contract_id.foreign_currency_id,
                        self.env.company,
                        fields.Date.today()
                    )
                val = {
                    'name': 'Discharge',
                    'code': 'DISCHARGE',
                    'input_type_id': discharge_type_id.id,
                    'amount': discharge_allowance,
                    'contract_id': payslip.employee_id.contract_id.id,
                }
                payslip.write({'input_line_ids': [(0, 0, val)]})

            if holiday_allowance:
                if payslip.contract_id.foreign_currency_id and payslip.contract_id.foreign_currency_id != self.company_currency_id:
                    holiday_allowance = self.company_currency_id._convert(
                        holiday_allowance,
                        payslip.contract_id.foreign_currency_id,
                        self.env.company,
                        fields.Date.today()
                    )
                val = {
                    'name': 'Holiday Allowance',
                    'code': 'REIMBURSEMENT',
                    'input_type_id': allowance_type_id.id,
                    'amount': holiday_allowance,
                    'contract_id': payslip.employee_id.contract_id.id,
                }
                payslip.write({'input_line_ids': [(0, 0, val)]})

            if penalty:
                if payslip.contract_id.foreign_currency_id and payslip.contract_id.foreign_currency_id != self.company_currency_id:
                    penalty = self.company_currency_id._convert(
                        penalty,
                        payslip.contract_id.foreign_currency_id,
                        self.env.company,
                        fields.Date.today()
                    )
                val = {
                    'name': 'Penalty',
                    'code': 'DEDUCTION',
                    'input_type_id': deduction_type_id.id,
                    'amount': penalty,
                    'contract_id': payslip.employee_id.contract_id.id,
                }
                payslip.write({'input_line_ids': [(0, 0, val)]})

            if shop_deduction:
                if payslip.contract_id.foreign_currency_id and payslip.contract_id.foreign_currency_id != self.company_currency_id:
                    shop_deduction = self.company_currency_id._convert(
                        shop_deduction,
                        payslip.contract_id.foreign_currency_id,
                        self.env.company,
                        fields.Date.today()
                    )
                val = {
                    'name': 'Shop Deduction',
                    'code': 'DEDUCTION',
                    'input_type_id': deduction_type_id.id,
                    'amount': shop_deduction,
                    'contract_id': payslip.employee_id.contract_id.id,
                }
                payslip.write({'input_line_ids': [(0, 0, val)]})

            if pre_payment_deduction:
                # if payslip.contract_id.foreign_currency_id and payslip.contract_id.foreign_currency_id != self.company_currency_id:
                #     pre_payment_deduction = self.company_currency_id._convert(
                #         pre_payment_deduction,
                #         payslip.contract_id.foreign_currency_id,
                #         self.env.company,
                #         fields.Date.today()
                #     )
                val = {
                    'name': 'Salary Pre Payment',
                    'code': 'DEDUCTION',
                    'input_type_id': deduction_type_id.id,
                    'amount': pre_payment_deduction,
                    'contract_id': payslip.employee_id.contract_id.id,
                }
                payslip.write({'input_line_ids': [(0, 0, val)]})

            if pending_salaries:
                if payslip.contract_id.foreign_currency_id and payslip.contract_id.foreign_currency_id != self.company_currency_id:
                    pending_salaries = self.company_currency_id._convert(
                        pending_salaries,
                        payslip.contract_id.foreign_currency_id,
                        self.env.company,
                        fields.Date.today()
                    )
                val = {
                    'name': 'Pending Salaries',
                    'code': 'REIMBURSEMENT',
                    'input_type_id': allowance_type_id.id,
                    'amount': pending_salaries,
                    'contract_id': payslip.employee_id.contract_id.id,
                }
                payslip.write({'input_line_ids': [(0, 0, val)]})

            # if not payslip.employee_id or not payslip.date_from or not payslip.date_to:
            #     continue
            #
            # employee = payslip.employee_id
            # date_from = payslip.date_from
            #
            # ttyme = datetime.combine(fields.Date.from_string(date_from), time.min)
            # locale = payslip.env.context.get('lang') or 'en_US'
            # payslip.name = _('Salary Slip of %s for %s') % (
            #     employee.name, tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale)))
            # payslip.company_id = employee.company_id

            # deduction = payslip.env['hr.earn.ded'].search(
            #     [('employee_id', '=', payslip.employee_id.id), ('state', 'in', ['approve']),
            #      ('balance_amount', '!=', 0)])
            # for d in deduction:
            #     total_paid = 0.0
            #     if d.is_recurring:
            #         if d.contract_id and d.type == 'deductions' and d.deduction_rule_id and d.deduction_rule_id.active:
            #             ded = payslip.env['hr.payslip.input.type'].search([('name', '=', 'Deduction')])
            #             val = {'name': d.deduction_rule_id.name or '',
            #                    'code': d.deduction_rule_id.code or '',
            #                    'input_type_id': ded.id,
            #                    'amount': d.deduction_amount,
            #                    'contract_id': d.contract_id.id,
            #                    'salary_rule_id': d.deduction_rule_id.id,
            #                    }
            #             payslip.write({'input_line_ids': [(0, 0, val)]})
            #         elif d.contract_id and d.type == 'earnings' and d.allowance_rule_id and d.allowance_rule_id.active:
            #             earning = payslip.env['hr.payslip.input.type'].search([('code', '=', 'REIMBURSEMENT')])
            #             val = {'name': d.allowance_rule_id.name or '',
            #                    'code': d.allowance_rule_id.code or '',
            #                    'amount': d.deduction_amount,
            #                    'input_type_id': earning.id,
            #                    'salary_rule_id': d.allowance_rule_id.id,
            #                    'contract_id': d.contract_id.id,
            #                    }
            #             payslip.write({'input_line_ids': [(0, 0, val)]})
            #     else:
            #         for i in d.deduction_lines:
            #             if i.state == 'active' or i.state == 'paid':
            #                 if i.paid:
            #                     total_paid += i.amount
            #                 if i.date <= payslip.date_to:
            #                     if total_paid == 0.0:
            #                         balance_amount = d.deduction_amount - i.amount
            #                     else:
            #                         balance_amount = d.deduction_amount - total_paid
            #                     if d.contract_id and d.type == 'deductions' and d.deduction_rule_id and d.deduction_rule_id.active:
            #                         ded = payslip.env['hr.payslip.input.type'].search([('name', '=', 'Deduction')])
            #                         val = {'name': d.deduction_rule_id.name or '',
            #                                'code': d.deduction_rule_id.code or '',
            #                                'input_type_id': ded.id,
            #                                'amount': i.amount,
            #                                'contract_id': d.contract_id.id,
            #                                'balance': balance_amount,
            #                                'salary_rule_id': d.deduction_rule_id.id,
            #                                'e_and_d_line_id': i.id,
            #                                }
            #                         payslip.write({'input_line_ids': [(0, 0, val)]})
            #                     elif d.contract_id and d.type == 'earnings' and d.allowance_rule_id and d.allowance_rule_id.active:
            #                         earning = payslip.env['hr.payslip.input.type'].search(
            #                             [('code', '=', 'REIMBURSEMENT')])
            #                         val = {'name': d.allowance_rule_id.name or '',
            #                                'code': d.allowance_rule_id.code or '',
            #                                'amount': i.amount,
            #                                'input_type_id': earning.id,
            #                                'salary_rule_id': d.allowance_rule_id.id,
            #                                'contract_id': d.contract_id.id,
            #                                'balance': balance_amount,
            #                                'e_and_d_line_id': i.id, }
            #                         payslip.write({'input_line_ids': [(0, 0, val)]})

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
    #                     if not rule.for_oman and payslip.employee_id.country_id.code != 'OM':
    #                         result[rule.code] = {
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
    #                         }
    #                     elif payslip.employee_id.country_id.code == 'OM':
    #                         result[rule.code] = {
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
    #                         }
    #         line_vals += list(result.values())
    #     return line_vals

    def action_print_payslip(self):
        """ Overridden to change payslip print """
        return self.env.ref('hr_payroll.action_report_payslip').report_action(self)

    def _action_create_account_move(self):
        """ Overridden to add multi currency handling """
        precision = self.env['decimal.precision'].precision_get('Payroll')

        # Add payslip without run
        payslips_to_post = self.filtered(lambda slip: not slip.payslip_run_id)

        # Adding pay slips from a batch and deleting pay slips with a batch that is not ready for validation.
        payslip_runs = (self - payslips_to_post).payslip_run_id
        for run in payslip_runs:
            if run._are_payslips_ready():
                payslips_to_post |= run.slip_ids

        # A payslip need to have a done state and not an accounting move.
        payslips_to_post = payslips_to_post.filtered(lambda slip: slip.state == 'done' and not slip.move_id)

        # Check that a journal exists on all the structures
        if any(not payslip.struct_id for payslip in payslips_to_post):
            raise ValidationError(_('One of the contract for these payslips has no structure type.'))
        if any(not structure.journal_id for structure in payslips_to_post.mapped('struct_id')):
            raise ValidationError(_('One of the payroll structures has no account journal defined on it.'))

        # Map all payslips by structure journal and pay slips month.
        # Case 1: Batch all the payslips together -> {'journal_id': {'month': slips}}
        # Case 2: Generate account move separately -> [{'journal_id': {'month': slip}}]
        if self.company_id.batch_payroll_move_lines:
            all_slip_mapped_data = defaultdict(lambda: defaultdict(lambda: self.env['hr.payslip']))
            for slip in payslips_to_post:
                all_slip_mapped_data[slip.struct_id.journal_id.id][
                    slip.date or fields.Date().end_of(slip.date_to, 'month')] |= slip
            all_slip_mapped_data = [all_slip_mapped_data]
        else:
            all_slip_mapped_data = [{
                slip.struct_id.journal_id.id: {
                    slip.date or fields.Date().end_of(slip.date_to, 'month'): slip
                }
            } for slip in payslips_to_post]

        for slip_mapped_data in all_slip_mapped_data:
            for journal_id in slip_mapped_data:  # For each journal_id.
                for slip_date in slip_mapped_data[journal_id]:  # For each month.
                    line_ids = []
                    debit_sum = 0.0
                    credit_sum = 0.0
                    date = slip_date

                    first_slip = slip_mapped_data[journal_id][slip_date][0]
                    currency_id = first_slip.currency_id.id if first_slip.currency_id else None

                    move_dict = {
                        'narration': '',
                        'ref': fields.Date().end_of(slip_mapped_data[journal_id][slip_date][0].date_to,
                                                    'month').strftime('%B %Y'),
                        'journal_id': journal_id,
                        'date': date,
                        'currency_id': currency_id
                    }

                    for slip in slip_mapped_data[journal_id][slip_date]:
                        move_dict['narration'] += plaintext2html(
                            slip.number or '' + ' - ' + slip.employee_id.name or '')
                        move_dict['narration'] += Markup('<br/>')
                        slip_lines = slip._prepare_slip_lines(date, line_ids)
                        line_ids.extend(slip_lines)

                    for line_id in line_ids:  # Get the debit and credit sum.
                        debit_sum += line_id['debit']
                        credit_sum += line_id['credit']

                    # The code below is called if there is an error in the balance between credit and debit sum.
                    if float_compare(credit_sum, debit_sum, precision_digits=precision) == -1:
                        slip._prepare_adjust_line(line_ids, 'credit', debit_sum, credit_sum, date)
                    elif float_compare(debit_sum, credit_sum, precision_digits=precision) == -1:
                        slip._prepare_adjust_line(line_ids, 'debit', debit_sum, credit_sum, date)

                    # Add accounting lines in the move
                    move_dict['line_ids'] = [(0, 0, line_vals) for line_vals in line_ids]
                    move = self._create_account_move(move_dict)
                    for slip in slip_mapped_data[journal_id][slip_date]:
                        slip.write({'move_id': move.id, 'date': date})
        return True

    def _prepare_line_values(self, line, account_id, date, debit, credit):
        """ Overridden to add multi currency handling """
        currency = self.currency_id or self.company_id.currency_id
        amount_currency = 0.0
        if self.currency_id and self.currency_id != self.company_id.currency_id:
            if debit > 0:
                amount_currency = debit
            else:
                amount_currency = -credit
            if debit:
                debit = self.currency_id._convert(amount_currency, self.company_currency_id, self.env.company,
                                                  fields.Date.today())
            if credit:
                credit = - self.currency_id._convert(amount_currency, self.company_currency_id, self.env.company,
                                                     fields.Date.today())

        if not self.company_id.batch_payroll_move_lines and line.code == "NET":
            partner = self.employee_id.work_contact_id
        else:
            partner = line.partner_id

        return {
            'name': line.name,
            'partner_id': partner.id,
            'account_id': account_id,
            'journal_id': line.slip_id.struct_id.journal_id.id,
            'date': date,
            'debit': debit,
            'credit': credit,
            'amount_currency': amount_currency,
            'currency_id': currency.id,
            'analytic_distribution': (line.salary_rule_id.analytic_account_id and {
                line.salary_rule_id.analytic_account_id.id: 100}) or
                                     (line.slip_id.contract_id.analytic_account_id.id and {
                                         line.slip_id.contract_id.analytic_account_id.id: 100})
        }

    def _get_worked_day_lines(self, domain=None, check_out_of_contract=True):
        """ Adding condition for taking worked days form employee entries for crew members """
        for payslip in self:
            res = super(HRPayslip, self)._get_worked_day_lines()
            if payslip.employee_id.crew:
                crew = self.env['hr.employee.entry'].search(
                    [('employee_id', '=', payslip.employee_id.id), ('start_date', '>=', payslip.date_from),
                     ('end_date', '<=', payslip.date_to), ('state', '=', 'approved')])
                duration = sum(crew.mapped('duration'))
                amount = 0
                if payslip.contract_id.daily_wage:
                    amount = payslip.contract_id.basic_per_day * duration
                else:
                    amount = payslip.contract_id.wage
                for line in res:
                    line.update({
                        'number_of_days': duration,
                        'amount': amount,
                    })
                return res
            else:
                return res

    def _get_rule_name(self, localdict, rule, employee_lang):
        """ Overridden to change rule name of net and gross salary """
        if localdict['result_name']:
            rule_name = localdict['result_name']
        elif rule.code in ['BASIC', 'GROSS', 'NET', 'DEDUCTION',
                           'REIMBURSEMENT']:  # Generated by default_get (no xmlid)
            if rule.code == 'BASIC':  # Note: Crappy way to code this, but _(foo) is forbidden. Make a method in master to be overridden, using the structure code
                if rule.name == "Double Holiday Pay":
                    rule_name = _("Double Holiday Pay")
                if rule.struct_id.name == "CP200: Employees 13th Month":
                    rule_name = _("Prorated end-of-year bonus")
                else:
                    rule_name = _('Basic Salary')
            elif rule.code == "GROSS":
                rule_name = _('Total')
            elif rule.code == "DEDUCTION":
                rule_name = _('Deduction')
            elif rule.code == "REIMBURSEMENT":
                rule_name = _('Allowances and Bonuses')
            elif rule.code == 'NET':
                rule_name = _('Paid Salary')
        else:
            rule_name = rule.with_context(lang=employee_lang).name
        return rule_name


class HRPayslipWorkedDays(models.Model):
    _inherit = 'hr.payslip.worked_days'
    _description = 'Payslip Worked Days'

    @api.depends('is_paid', 'is_credit_time', 'number_of_hours', 'payslip_id', 'contract_id.wage',
                 'payslip_id.sum_worked_hours')
    def _compute_amount(self):
        """ Overridden to compute amount based on worked days for crew with daily wage """
        for worked_days in self:
            if worked_days.payslip_id.edited or worked_days.payslip_id.state not in ['draft', 'verify']:
                continue
            if not worked_days.contract_id or worked_days.code == 'OUT' or worked_days.is_credit_time:
                worked_days.amount = 0
                continue
            if worked_days.payslip_id.wage_type == "hourly":
                worked_days.amount = worked_days.payslip_id.contract_id.hourly_wage * worked_days.number_of_hours if worked_days.is_paid else 0
            else:
                if worked_days.payslip_id.contract_id.daily_wage:
                    worked_days.amount = worked_days.payslip_id.contract_id.basic_per_day * worked_days.number_of_days
                else:
                    worked_days.amount = worked_days.payslip_id.contract_id.contract_wage * worked_days.number_of_hours / (
                            worked_days.payslip_id.sum_worked_hours or 1) if worked_days.is_paid else 0
