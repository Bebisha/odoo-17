# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SalaryPrePayment(models.Model):
    _name = 'salary.pre.payment'
    _description = 'salary.pre.payment'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    amount = fields.Float(string='Advance Amount', required=True)
    paid_date = fields.Date(string='Paid Date', required=True)
    name = fields.Char(string='Description')
    considered_in_payslip = fields.Boolean(string='Considered in Payslip')
    state = fields.Selection([('draft', "Draft"), ('approved', "Approved")],
                             string="State", default='draft')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.user.company_id.currency_id)
    company_currency_id = fields.Many2one('res.currency', string='Company Currency',
                                          default=lambda self: self.env.user.company_id.currency_id, readonly=True)
    amount_in_currency = fields.Float(string='Amount In USD')
    salary_pre_payment_request_id = fields.Many2one('salary.pre.payment.request', string='Salary Pre Payment Request')

    def action_approve(self):
        """ Approval process, creates other input for the amount to be deducted
                from salary and create a deduction for the same """
        for entry in self:
            if entry.state == 'draft':
                # deduction_rule_id = self.env['hr.salary.rule'].search([('code', '=', 'ADVSAL')])
                # deduction = {
                #     'employee_id': entry.employee_id.id,
                #     'contract_id': entry.employee_id.contract_id.id,
                #     'type': 'deductions',
                #     'deduction_rule_id': deduction_rule_id.id,
                #     'deduction_amount': entry.amount,
                #     'payment_date': entry.paid_date,
                # }
                # deduction_id = self.env['hr.deduction'].create(deduction)
                # deduction_id.sudo().compute_installment()
                # deduction_id.sudo().action_validate()
                # deduction_id.sudo().action_approve()

                entry.write({
                    'considered_in_payslip': True,
                    'state': 'approved'
                })
