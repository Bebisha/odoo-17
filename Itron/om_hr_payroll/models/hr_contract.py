# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from num2words import num2words

from odoo import api, fields, models, _


class HrContract(models.Model):
    """
    Employee contract based on the visa, work permits
    allows to configure different Salary structure
    """
    _inherit = 'hr.contract'
    _description = 'Employee Contract'

    struct_id = fields.Many2one('hr.payroll.structure', string='Salary Structure')
    schedule_pay = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semi-annually', 'Semi-annually'),
        ('annually', 'Annually'),
        ('weekly', 'Weekly'),
        ('bi-weekly', 'Bi-weekly'),
        ('bi-monthly', 'Bi-monthly'),
    ], string='Scheduled Pay', index=True, default='monthly',
        help="Defines the frequency of the wage payment.")
    resource_calendar_id = fields.Many2one(required=True, help="Employee's working schedule.")
    hra = fields.Monetary(string='HRA', help="House rent allowance.")
    utility_exp_allowance = fields.Monetary(string='Utility Expenses Allowances', help="Utility Expenses Allowances.")
    telephone_expense = fields.Monetary(string='Telephone Expenses', help="Telephone Expenses.")
    transport_allowance = fields.Monetary(string="Transport Allowance", help="Transport allowance")
    total_con = fields.Float(string='Total', compute='_compute_total_con')
    salary_rev_date = fields.Date(string='Salary Updated on', required=True, copy=False)
    salary_history_line = fields.One2many('salary.history.line', 'contract_id', copy=False)

    @api.depends('wage', 'hra', 'transport_allowance', 'utility_exp_allowance', 'telephone_expense')
    def _compute_total_con(self):
        for record in self:
            record.total_con = (
                    record.wage +
                    record.hra +
                    record.transport_allowance +
                    record.utility_exp_allowance +
                    record.telephone_expense
            )

    type_id = fields.Many2one('hr.contract.type', string="Employee Category",
                              required=True, help="Employee category",
                              default=lambda self: self.env['hr.contract.type'].search([], limit=1))

    def get_all_structures(self):
        """
        @return: the structures linked to the given contracts, ordered by hierachy (parent=False first,
                 then first level children and so on) and without duplicata
        """
        structures = self.mapped('struct_id')
        if not structures:
            return []
        # YTI TODO return browse records
        return list(set(structures._get_parent_structure().ids))

    def get_attribute(self, code, attribute):
        return self.env['hr.contract.advantage.template'].search([('code', '=', code)], limit=1)[attribute]

    def set_attribute_value(self, code, active):
        for contract in self:
            if active:
                value = self.env['hr.contract.advantage.template'].search([('code', '=', code)], limit=1).default_value
                contract[code] = value
            else:
                contract[code] = 0.0

    def action_update_salary_details(self):
        """
        Wizard to display and update salary details.
        """
        self.ensure_one()
        return {
            'name': _('Update Salary'),
            'type': 'ir.actions.act_window',
            'res_model': 'update.salary.details',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_contract_id': self.id, 'default_wage': self.wage, 'default_hra': self.hra,
                        'default_utility_exp_allowance': self.utility_exp_allowance,
                        'default_telephone_expense': self.telephone_expense,
                        'default_transport_allowance': self.transport_allowance,
                      }
        }


class HrContractAdvantageTemplate(models.Model):
    _name = 'hr.contract.advantage.template'
    _description = "Employee's Advantage on Contract"

    name = fields.Char('Name', required=True)
    code = fields.Char('Code', required=True)
    lower_bound = fields.Float('Lower Bound', help="Lower bound authorized by the employer for this advantage")
    upper_bound = fields.Float('Upper Bound', help="Upper bound authorized by the employer for this advantage")
    default_value = fields.Float('Default value for this advantage')


class SalaryHistoryLine(models.Model):
    """ Model to display the salary history of an employee."""
    _name = 'salary.history.line'
    _description = 'salary.history.line'

    contract_id = fields.Many2one('hr.contract', string='Contract', copy=False)
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company', required=True, readonly=True,
        default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related="company_id.currency_id")
    allow_hra = fields.Monetary(string='HRA', help="House rent allowance.", readonly=True)
    utility_exp_allowance = fields.Monetary(string='Utility Expenses Allowances', readonly=True,
                                            help="Utility Expenses Allowances.")
    telephone_expense = fields.Monetary(string='Telephone Expenses', readonly=True, help="Telephone Expenses.")
    transport_allowance = fields.Monetary(string="Transport Allowance", readonly=True, help="Transport allowance")
    total_con = fields.Float(string='Total', readonly=True)
    salary_rev_date = fields.Date(readonly=True, string='Date', copy=False)
    wage = fields.Monetary('Wage', tracking=True, help="Employee's monthly gross wage.",
                           group_operator="avg")
