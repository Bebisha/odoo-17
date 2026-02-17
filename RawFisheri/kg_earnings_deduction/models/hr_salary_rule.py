# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    is_earn_deduct = fields.Boolean(string="Earnings and Deduction")
    gratuity_next_month = fields.Boolean(string="Balance Payment (gratuity)")
    input_ids = fields.One2many('hr.rule.input', 'input_id', string='Inputs', copy=True)


class HrRuleInput(models.Model):
    _name = 'hr.rule.input'
    _description = 'Salary Rule Input'

    input_id = fields.Many2one('hr.salary.rule', string='Salary Rule Input', required=True)