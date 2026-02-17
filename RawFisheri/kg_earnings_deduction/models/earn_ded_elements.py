# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class EarnDedElements(models.Model):
    _name = "earn.ded.elements"
    _description = "E&D Elements"

    name = fields.Char(string="Name")
    short_code = fields.Char('Code', copy=False)
    salary_struct_id = fields.Many2one('hr.payroll.structure', string="Structure")
    element_type = fields.Selection([('earn', 'Earnings'), ('ded', 'Deduction')])
    rule_id = fields.Many2one('hr.salary.rule', string="Rule Id", copy=False)
    active = fields.Boolean('Active')
    _sql_constraints = [
        ('unique_short_code', 'unique(short_code)', 'The code must be unique!'),
    ]

    @api.onchange('short_code')
    def set_caps(self):
        for rec in self:
            if rec.short_code:
                upper_case_short_code = rec.short_code.upper()
                regex = "[@!#$%^&*()[<>?/|}]{~:=,+-]."
                if any(sp in rec.short_code for sp in regex):
                    raise UserError('No Special Characters Allowed !')
                elif self.search([('short_code', '=', upper_case_short_code)], limit=1):
                    raise UserError(
                        'This code has been already assigned with an element..Please try another one !!')
                else:
                    rec.short_code = upper_case_short_code

    def apply_rule(self):
        """ Creating Salary Rule from earnings and deduction elements """
        rule_cat_domain = [('code', '=', 'DED')] if self.element_type == 'ded' else [('code', '=', 'ALW')]
        rule_cat_id = self.env['hr.salary.rule.category'].search(rule_cat_domain, limit=1)
        code = self.short_code
        if self.element_type == 'ded':
            operator = '-inputs[\'{}\'].amount'.format(code)
        else:
            operator = 'inputs[\'{}\'].amount > 0.0'.format(code)
        # python_expression = 'result = -min(result_rules['BASIC']['total']'.format(code, operator, code)
        # python_expression = 'result = inputs.{} and {} (inputs.{}.amount)'.format(code, operator,code)
        python_code = 'result = {1} if \'{0}\' in inputs else False'.format(code, operator)

        python_expression = 'result = {1} if \'{0}\' in inputs else False'.format(code, operator)

        vals = {
            'name': self.name,
            'struct_id': self.salary_struct_id.id,
            'category_id': rule_cat_id.id,
            'code': code,
            'active': True,
            'is_earn_deduct': True,
            'amount_select': 'code',
            'condition_select': 'python',
            'condition_python': python_code,
            'amount_python_compute': python_expression
        }
        if not self.rule_id:
            salary_rule_exist = self.env['hr.salary.rule'].search([('code', '=', self.short_code)], limit=1)
            if not salary_rule_exist:
                rule_id = self.env['hr.salary.rule'].create(vals)
                self.rule_id = rule_id.id
                self.salary_struct_id.rule_ids = [(4, self.rule_id.id)]
            else:
                self.rule_id = salary_rule_exist.id
                self.salary_struct_id.rule_ids = [(4, self.rule_id.id)]
        else:
            if not self.short_code == self.rule_id.code or not self.check_rule_match():
                self.rule_id.write(vals)
            if not self.rule_id.active:
                self.rule_id.active = True
            if not self.rule_id.id in self.salary_struct_id.rule_ids.ids:
                self.salary_struct_id.rule_ids = [(4, self.rule_id.id)]
        try:
            self.active = True if not self.active else False
        except Exception as e:
            return e

    def copy(self, default=None):
        default = dict(default or {})
        default.update(name=_("%s (copy)") % self.name)
        return super().copy(default)

    def check_rule_match(self):
        if self.rule_id:
            if self.element_type == 'earn' and self.rule_id.category_id.code == 'ALW' or self.element_type == 'ded' and self.rule_id.category_id.code == 'DED':
                return True
            else:
                return False

    def disable_rule(self):
        for rec in self:
            rec.rule_id.active = False
            rec.active = False

    def action_archive(self):
        self.rule_id.active = False
        return super(EarnDedElements, self).action_archive()

    def action_unarchive(self):
        [rec.apply_rule() for rec in self]
        return super(EarnDedElements, self).action_unarchive()
