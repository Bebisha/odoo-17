# -*- coding: utf-8 -*-
from odoo import api, fields, models


class UpdateSalaryDetails(models.TransientModel):
    """ Model to update salary details and manage the salary of an employee."""
    _name = 'update.salary.details'
    _description = 'update.salary.details'

    contract_id = fields.Many2one('hr.contract', string='Contract', readonly=True)
    wage = fields.Monetary('Wage', tracking=True, help="Employee's monthly gross wage.",
                           group_operator="avg")
    hra = fields.Monetary(string='HRA', help="House rent allowance.")
    utility_exp_allowance = fields.Monetary(string='Utility Expenses Allowances', help="Utility Expenses Allowances.")
    telephone_expense = fields.Monetary(string='Telephone Expenses', help="Telephone Expenses.")
    transport_allowance = fields.Monetary(string="Transport Allowance", help="Transport allowance")
    salary_rev_date = fields.Date(required=True, string='Salary Revised On', copy=False)
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company', required=True, readonly=True,
        default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related="company_id.currency_id")

    def action_update_salary(self):
        """Function triggered by the button to update the salary details of an employee."""
        for rec in self:
            if rec.contract_id.salary_rev_date and (
                    not rec.contract_id.salary_history_line or
                    rec.contract_id.salary_rev_date != rec.contract_id.salary_history_line[-1].salary_rev_date
            ):
                rec.contract_id.write({
                    'salary_history_line': [(0, 0, {
                        'wage': rec.contract_id.wage,
                        'allow_hra': rec.contract_id.hra,
                        'utility_exp_allowance': rec.contract_id.utility_exp_allowance,
                        'telephone_expense': rec.contract_id.telephone_expense,
                        'transport_allowance': rec.contract_id.transport_allowance,
                        'total_con': rec.contract_id.total_con,
                        'salary_rev_date': rec.contract_id.salary_rev_date,
                    })]
                })
            if rec.salary_rev_date != rec.contract_id.salary_rev_date:
                rec.contract_id.write({
                    'wage': rec.wage,
                    'hra': rec.hra,
                    'utility_exp_allowance': rec.utility_exp_allowance,
                    'telephone_expense': rec.telephone_expense,
                    'transport_allowance': rec.transport_allowance,
                    'salary_rev_date': rec.salary_rev_date,
                })
