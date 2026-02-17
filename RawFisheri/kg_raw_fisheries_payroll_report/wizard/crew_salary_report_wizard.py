# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import fields, models, api, _


class CrewSalaryReportWizard(models.TransientModel):
    _name = 'crew.salary.report.wizard'
    _description = 'crew.salary.report.wizard'

    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    vessel_id = fields.Many2one('sponsor.sponsor', string='Vessel')

    def action_view_report(self):
        for crew in self:
            pending_salary_amount = 0.00
            total_salary_amount = 0.00
            today = datetime.today().date()
            if crew.vessel_id:
                crew_members = self.env['hr.employee'].search(
                    [('crew', '!=', False), ('sponsor_name', '=', crew.vessel_id.id), ('contract_id', '!=', False)])
            else:
                crew_members = self.env['hr.employee'].search([('crew', '!=', False), ('contract_id', '!=', False)])
            if crew_members:
                crew_members_ids = crew_members.filtered(
                    lambda x: (x.sign_on_date and x.sign_off_date and (
                            x.sign_on_date <= self.end_date and x.sign_off_date >= self.start_date)) or (
                                          x.sign_on_date and not x.sign_off_date and (
                                          self.start_date <= x.sign_on_date <= self.end_date)))

                domain_list = []
                duration = 0
                for crews in crew_members:
                    contract = crews.contract_id
                    employee_entries = self.env['hr.employee.entry'].search(
                        [('employee_id', '=', crews.id), ('start_date', '>=', crew.start_date),
                         ('end_date', '<=', crew.end_date),('state','=','approved')])
                    discharge = 0
                    bonus = 0
                    shop_deduction = 0
                    overtime = 0
                    holiday_allowance = 0
                    penalty = 0

                    for employee_entry in employee_entries:
                        pending_salary_id = self.env['pending.salary'].search(
                            [('employee_id', '=', crews.id), ('settlement_date', '>=', crew.start_date),
                             ('settlement_date', '<=', crew.end_date), ('state', '=', 'approved')])
                        if pending_salary_id:
                            pending_salary_amount = sum(pending_salary_id.mapped('amount'))

                        contract_end_date = contract.date_end if contract and contract.date_end else employee_entry.end_date
                        discharge += employee_entry.discharge_qty
                        bonus += employee_entry.bonus
                        shop_deduction += employee_entry.shop_deduction
                        overtime += employee_entry.over_time
                        holiday_allowance += employee_entry.holiday_allowance
                        penalty += employee_entry.penalty
                        # duration = (employee_entry.end_date - employee_entry.start_date).days + 1 if contract_end_date > today else (contract_end_date - employee_entry.start_date).days + 1
                        duration = employee_entry.duration

                    basic_wage = contract.basic_per_day * duration if contract.daily_wage else contract.wage

                    total_salary_amount = basic_wage + contract.housing_allowance + contract.travel_allowance + contract.other_allowance + contract.extra_income + contract.fixed_sea_allowance + discharge - shop_deduction + overtime + holiday_allowance + pending_salary_amount + bonus - penalty

                    if employee_entries:
                        vals = {
                            'employee_id': crews.id,
                            'start_date': crew.start_date,
                            'end_date': crew.end_date,
                            'basic_wage': basic_wage,
                            'house_allowance': contract.housing_allowance,
                            'transport_allowance': contract.travel_allowance,
                            'other_allowance': contract.other_allowance,
                            'extra_income': contract.extra_income,
                            'fixed_sea_allowance': contract.fixed_sea_allowance,
                            'discharge': discharge,
                            'shop_deduction': shop_deduction,
                            'overtime': overtime,
                            'holiday_allowance': holiday_allowance,
                            'bonus': bonus,
                            'pending_salary_amount': pending_salary_amount,
                            'penalty': penalty,
                            'total_salary_amount': total_salary_amount,
                        }
                        report = self.env['crew.salary.report'].create(vals)
                        domain_list.append(report.id)

                return {
                    'name': _('Crew Salary Report'),
                    'view_type': 'form',
                    'view_mode': 'tree,''pivot',
                    'domain': [('id', 'in', domain_list)],
                    'context': {
                        'search_default_groupby_department_id': 1
                    },
                    'res_model': 'crew.salary.report',
                    'type': 'ir.actions.act_window',
                    'target': 'main',
                }
