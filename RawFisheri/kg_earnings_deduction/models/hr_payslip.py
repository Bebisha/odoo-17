# -*- coding: utf-8 -*-
from datetime import datetime, time, timezone

import babel

from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError


class HrPayslipDeduction(models.Model):
    _inherit = 'hr.payslip'

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
    #         deduction = record.env['hr.earn.ded'].search(
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

    def _get_payslip_lines(self):
        line_vals = []
        for payslip in self:
            if not payslip.contract_id:
                raise UserError(
                    _("There's no contract set on payslip %s for %s. Check that there is at least a contract set on the employee form.",
                      payslip.name, payslip.employee_id.name))

            localdict = self.env.context.get('force_payslip_localdict', None)
            if localdict is None:
                localdict = payslip._get_localdict()

            rules_dict = localdict['rules']
            result_rules_dict = localdict['result_rules']

            blacklisted_rule_ids = self.env.context.get('prevent_payslip_computation_line_ids', [])

            result = {}
            for rule in sorted(payslip.struct_id.rule_ids, key=lambda x: x.sequence):
                if rule.id in blacklisted_rule_ids:
                    continue
                localdict.update({
                    'result': None,
                    'result_qty': 1.0,
                    'result_rate': 100,
                    'result_name': False
                })
                if rule._satisfy_condition(localdict):
                    employee_lang = payslip.employee_id.lang
                    context = {'lang': employee_lang}
                    if rule.code in localdict['same_type_input_lines']:
                        for multi_line_rule in localdict['same_type_input_lines'][rule.code]:
                            if 'inputs' not in localdict:
                                localdict['inputs'] = {}

                            localdict['inputs'][rule.code] = multi_line_rule
                            amount, qty, rate = rule._compute_rule(localdict)
                            tot_rule = amount * qty * rate / 100.0
                            localdict = rule.category_id._sum_salary_rule_category(localdict,
                                                                                   tot_rule)
                            rule_name = payslip._get_rule_name(localdict, rule, employee_lang)
                            line_vals.append({
                                'sequence': rule.sequence,
                                'code': rule.code,
                                'name': rule_name,
                                'salary_rule_id': rule.id,
                                'contract_id': localdict['contract'].id,
                                'employee_id': localdict['employee'].id,
                                'amount': amount,
                                'quantity': qty,
                                'rate': rate,
                                'slip_id': payslip.id,
                            })
                    else:
                        amount, qty, rate = rule._compute_rule(localdict)
                        previous_amount = localdict.get(rule.code, 0.0)
                        tot_rule = amount * qty * rate / 100.0
                        localdict[rule.code] = tot_rule
                        result_rules_dict[rule.code] = {'total': tot_rule, 'amount': amount, 'quantity': qty,
                                                        'rate': rate}
                        rules_dict[rule.code] = rule
                        localdict = rule.category_id._sum_salary_rule_category(localdict, tot_rule - previous_amount)
                        rule_name = payslip._get_rule_name(localdict, rule, employee_lang)
                        result[rule.code] = {
                            'sequence': rule.sequence,
                            'code': rule.code,
                            'name': rule_name,
                            'salary_rule_id': rule.id,
                            'contract_id': localdict['contract'].id,
                            'employee_id': localdict['employee'].id,
                            'amount': amount,
                            'quantity': qty,
                            'rate': rate,
                            'slip_id': payslip.id,
                        }
            line_vals += list(result.values())
        return line_vals

    @api.model
    def get_contract(self, employee, date_from, date_to):
        """
        @param employee: recordset of employee
        @param date_from: date field
        @param date_to: date field
        @return: returns the ids of all the contracts for the given employee that need to be considered for the given dates
        """
        clause_1 = ['&', ('date_end', '<=', date_to), ('date_end', '>=', date_from)]
        clause_2 = ['&', ('date_start', '<=', date_to), ('date_start', '>=', date_from)]
        clause_3 = ['&', ('date_start', '<=', date_from), '|', ('date_end', '=', False), ('date_end', '>=', date_to)]
        clause_final = [('employee_id', '=', employee.id), ('state', '=', 'open'), '|',
                        '|'] + clause_1 + clause_2 + clause_3
        return self.env['hr.contract'].search(clause_final).ids

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
        for contract in contracts.filtered(lambda contract: contract.resource_calendar_id):
            day_from = datetime.combine(fields.Date.from_string(date_from), time.min)
            day_to = datetime.combine(fields.Date.from_string(date_to), time.max)
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

def action_register_payment(self):
    for record in self:
        res = super(HrPayslipDeduction, record).action_register_payment()
        for inp in record.input_line_ids:
            if inp.e_and_d_line_id:
                inp.e_and_d_line_id.write({'state': 'paid',
                                           'paid': True})
        return res


class HrPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'
    _description = 'Payslip Input'

    balance = fields.Float(string="Balance")
    code = fields.Char(related='input_type_id.code', required=True,
                       help="The code that can be used in the salary rules")
    salary_rule_id = fields.Many2one("hr.salary.rule", string="Salary Rule")
    e_and_d_line_id = fields.Many2one("hr.earn.ded.line", string="E & D")