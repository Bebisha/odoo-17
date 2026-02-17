# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class CrewSalaryReport(models.Model):
    _name = 'crew.salary.report'
    _description = 'crew.salary.report'

    employee_id = fields.Many2one('hr.employee', string='Employee')
    vessel_id = fields.Many2one('sponsor.sponsor', string='Vessel', related='employee_id.sponsor_name', store=True)
    department_id = fields.Many2one('hr.department', string='Department', related='employee_id.department_id',
                                    store=True)
    basic_wage = fields.Float(string='Basic Salary')
    house_allowance = fields.Float(string='Housing Allowance')
    transport_allowance = fields.Float(string='Transport Allowance')
    other_allowance = fields.Float(string='Other Allowance')
    extra_income = fields.Float(string='Other Income')
    discharge = fields.Float(string='Discharge')
    fixed_sea_allowance = fields.Float(string='Fixed Sea Allowance')
    shop_deduction = fields.Float(string='Shop Deduction')
    overtime = fields.Float(string='Overtime')
    holiday_allowance = fields.Float(string='Holiday Allowance')
    bonus = fields.Float(string='Extra Income')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    pending_salary_amount = fields.Float(string="Pending Salary")
    penalty = fields.Float(string="Penalty")
    total_salary_amount = fields.Float(string="Total Salary")

    def create_final_entry(self):
        vessel_id = self[0].vessel_id.id
        start_date = self[0].start_date
        end_date = self[0].end_date

        lines = []
        for crew in self:
            vals = {
                'employee_id': crew.employee_id.id,
                'basic_wage': crew.basic_wage,
                'house_allowance': crew.house_allowance,
                'transport_allowance': crew.transport_allowance,
                'other_allowance': crew.other_allowance,
                'extra_income': crew.extra_income,
                'fixed_sea_allowance': crew.fixed_sea_allowance,
                'discharge': crew.discharge,
                'shop_deduction': crew.shop_deduction,
                'overtime': crew.overtime,
                'holiday_allowance': crew.holiday_allowance,
                'bonus': crew.bonus,
            }
            lines.append((0, 0, vals))

        report = self.env['final.crew.salary.monthly'].create({
            'vessel_id': vessel_id,
            'start_date': start_date,
            'end_date': end_date,
            'final_crew_monthly_line_ids': lines,
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'final.crew.salary.monthly',
            'res_id': report.id,
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'current',
        }
