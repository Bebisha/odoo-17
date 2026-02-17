# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools.populate import compute


class HRContract(models.Model):
    _inherit = 'hr.contract'

    sponsor_name = fields.Many2one('sponsor.sponsor', 'Vessel')
    housing_allowance = fields.Float(string='Housing Allowance')
    travel_allowance = fields.Float(string='Transport Allowance')
    fixed_sea_allowance = fields.Float(string='Fixed Sea Allowance')
    other_allowance = fields.Float(string='Other Allowance')
    extra_income = fields.Float(string='Other Income')
    total_salary = fields.Float(string='Total Salary')
    ctc_month = fields.Monetary(string="Month Wage", compute="compute_ctc_wage")
    ctc_year = fields.Monetary(string="Year Wage", compute="compute_ctc_wage")
    daily_wage = fields.Boolean(string="Daily Wage")
    basic_per_day = fields.Float(string="Basic Per Day")
    employee_no = fields.Char(string="Employee No.", related="employee_id.employee_no")
    has_pasi = fields.Boolean(string='Has Pasi?')
    pasi_percentage = fields.Float(string='Pasi Percentage')
    pasi_deduction = fields.Float(string='Pasi', compute='_compute_pasi_deduction')
    foreign_currency_id = fields.Many2one('res.currency', string="Currency",
                                          default=lambda self: self.env.company.currency_id)
    sign_on_off_id = fields.Many2one("sign.on.off", string="Sign On/Off")

    @api.onchange('daily_wage', 'basic_per_day')
    def _onchange_basic_per_day(self):
        """ To calculate monthly wage from basic per day """
        for contract in self:
            if contract.daily_wage:
                contract.wage = contract.basic_per_day * 31

    @api.depends('wage', 'housing_allowance', 'travel_allowance', 'extra_income', 'other_allowance')
    def compute_ctc_wage(self):
        """To compute monthly and yearly CTC"""
        for contract in self:
            contract.ctc_month = contract.wage + contract.housing_allowance + contract.travel_allowance + contract.extra_income + contract.other_allowance + contract.fixed_sea_allowance
            contract.ctc_year = contract.ctc_month * 12

    @api.depends('pasi_percentage', 'wage', 'housing_allowance', 'travel_allowance')
    def _compute_pasi_deduction(self):
        """ To compute the pasi deduction for locals """
        for contract in self:
            if contract.has_pasi:
                pasi_value = contract.wage + contract.housing_allowance + contract.travel_allowance
                pasi_total = (pasi_value * contract.pasi_percentage) / 100
                contract.write({
                    'pasi_deduction': pasi_total,
                })
            else:
                contract.write({
                    'pasi_deduction': 0,
                })
