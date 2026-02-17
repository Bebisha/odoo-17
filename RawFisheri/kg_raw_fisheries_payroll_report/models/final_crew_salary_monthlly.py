# -*- coding: utf-8 -*-
from odoo import fields, models, api, _

class FinalCrewSalaryMonthly(models.Model):
    _name = 'final.crew.salary.monthly'
    _description = 'final.crew.salary.monthly'

    vessel_id = fields.Many2one('sponsor.sponsor', string='Vessel')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    name = fields.Char(string='Reference', default='New')
    final_crew_monthly_line_ids = fields.One2many('final.crew.salary.monthly.line','final_crew_monthly_line_id', string='Lines')

    @api.model
    def create(self, vals):
        """ Final Crew Salary Monthly Sequence Number Generation """
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'final.crew.salary.report.sequence') or _('New')
        return super(FinalCrewSalaryMonthly, self).create(vals)

class FinalCrewSalaryMonthlyLine(models.Model):
    _name = 'final.crew.salary.monthly.line'
    _description = 'final.crew.salary.monthly.line'

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
    final_crew_monthly_line_id = fields.Many2one('final.crew.salary.monthly', string='Final Crew Salary Monthly')
