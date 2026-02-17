# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SalaryPrePaymentRequest(models.Model):
    _name = 'salary.pre.payment.request'
    _description = 'salary.pre.payment.request'

    name = fields.Char(string='Reference')
    # employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    # employee_ids = fields.Many2many('hr.employee', string='Employee', required=True)
    # description = fields.Char(string='Description')
    date = fields.Date(string='Date', required=True)
    # advance_amount = fields.Float(string='Advance Amount')
    state = fields.Selection([('draft', "Draft"), ('requested', "Requested")], string="State", default='draft')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.user.company_id.currency_id)
    company_currency_id = fields.Many2one('res.currency', string='Company Currency',
                                          default=lambda self: self.env.user.company_id.currency_id, readonly=True)
    # amount_in_currency = fields.Float(string='Amount In USD', compute='_compute_amount_in_currency')
    salary_pre_payment_request_line_ids = fields.One2many('salary.pre.payment.request.line',
                                                          'salary_pre_payment_request_id',
                                                          string='Salary Pre Payment Request Line')
    salary_pre_payment_ids = fields.Many2many('salary.pre.payment', string='Salary Pre Payments')
    pre_payment_count = fields.Integer(compute='_compute_pre_payment_count')

    @api.model
    def create(self, vals):
        """ Salary Pre Payment Request sequence number generation """
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'salary.pre.payment.sequence') or _('New')
        return super(SalaryPrePaymentRequest, self).create(vals)

    @api.depends('salary_pre_payment_ids')
    def _compute_pre_payment_count(self):
        for request in self:
            request.pre_payment_count = len(request.salary_pre_payment_ids)

    def action_open_salary_pre_payment(self):
        """ Smart Button to return the salary pre payments associated with a request """
        for request in self:
            return {
                "type": "ir.actions.act_window",
                "res_model": "salary.pre.payment",
                "views": [[False, "tree"]],
                "domain": [['id', 'in', request.salary_pre_payment_ids.ids]],
                "name": "Salary Pre Payments",
            }

    def action_request(self):
        """ Button action to submit Salary Pre Payment Request """
        for request in self:
            if request.state == 'draft':
                salary_pre_payment_list = []
                for line in request.salary_pre_payment_request_line_ids:
                    vals = {
                        'employee_id': line.employee_id.id,
                        'name': line.description,
                        'amount': line.advance_amount,
                        'paid_date': request.date,
                        'currency_id': request.currency_id.id,
                        'amount_in_currency': line.amount_in_currency,
                        'salary_pre_payment_request_id': request.id,
                    }

                    salary_pre_payment_id = self.env['salary.pre.payment'].sudo().create(vals)
                    salary_pre_payment_list.append(salary_pre_payment_id.id)

                request.write({
                    'salary_pre_payment_ids': [(6, 0, salary_pre_payment_list)],
                    'state': 'requested',
                })


class SalaryPrePaymentRequestLine(models.Model):
    _name = 'salary.pre.payment.request.line'
    _description = 'salary.pre.payment.request.line'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    advance_amount = fields.Float(string='Advance Amount')
    amount_in_currency = fields.Float(string='Amount In USD', compute='_compute_amount_in_currency')
    description = fields.Char(string='Description')
    vessel_id = fields.Many2one('sponsor.sponsor', string="Vessel", related="employee_id.sponsor_name")
    factory_manager_ids = fields.Many2many(related='employee_id.factory_manager_ids', string="Factory Manager")
    salary_pre_payment_request_id = fields.Many2one('salary.pre.payment.request')

    @api.depends('salary_pre_payment_request_id.currency_id', 'advance_amount')
    def _compute_amount_in_currency(self):
        """ Computing Foreign Currency Amount from Base Currency """
        for line in self:
            if line.salary_pre_payment_request_id.currency_id == line.salary_pre_payment_request_id.company_currency_id:
                line.write({
                    'amount_in_currency': line.advance_amount,
                })
            else:
                amount = line.salary_pre_payment_request_id.currency_id._convert(line.advance_amount,
                                                                                 line.employee_id.contract_id.currency_id,
                                                                                 self.env.company,
                                                                                 fields.Date.today())
                line.write({
                    'amount_in_currency': amount,
                })
