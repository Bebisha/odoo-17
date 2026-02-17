# -*- coding: utf-8 -*-

from datetime import timedelta, date

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _


class ManagementCost(models.Model):
    """ To view the management cost report """
    _name = 'management.cost'
    _description = 'management.cost'

    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    analytic_account_line_id = fields.Many2one('account.analytic.line', string='Analytic Account Line')
    date = fields.Date(string='Date')
    amount = fields.Float(string='Amount')
    account_id = fields.Many2one('account.account', string='Account')
    type = fields.Selection([('income', 'Income'), ('expense', 'Expense'),('cor', 'Cost Of Revenue'), ('oin', 'Other Income'), ('dep', 'Depreciation')], string='Type',
                            store=True)

    @api.depends('account_id')
    def _compute_type(self):
        """Classify account as Income or Expense based on its type."""
        for record in self:
            if record.account_id.account_type in ('income', 'other_income'):
                record.type = 'income'
            elif record.account_id.account_type == 'expense':
                record.type = 'expense'
            else:
                record.type = False

    def load_analytic_account_details(self):
        """ Function to load data in the pivot view """
        today = date.today()
        first_day = today.replace(day=1)
        last_day = first_day + relativedelta(months=1) - timedelta(days=1)

        analytic_lines = self.env['account.analytic.line'].sudo().search([
            ('account_id.show_in_mc', '=', True),
            ('date', '>=', first_day),
            ('date', '<=', last_day)
        ])

        aggregated_data = {}
        for line in analytic_lines:
            key = (line.date, line.account_id.id, line.move_line_id.account_id.account_type)
            if key not in aggregated_data:
                aggregated_data[key] = 0.0
            aggregated_data[key] += line.amount

        domain_list = []
        for (record_date, analytic_account_id, account_type), total_amount in aggregated_data.items():
            report_record = self.env['management.cost'].sudo().create({
                'date': record_date,
                'analytic_account_id': analytic_account_id,
                'amount': total_amount,
                'type': 'income' if account_type in ('income',
                                                     'other_income') else 'cor' if account_type == 'expense_direct_cost' else 'oin' if account_type == 'income_other' else 'dep' if account_type == 'expense_depreciation' else 'expense',

            })
            domain_list.append(report_record.id)

        return {
            'name': _('Management Cost'),
            'view_type': 'form',
            'view_mode': 'pivot,tree',
            'domain': [('id', 'in', domain_list)],
            'context': {
                'search_default_groupby_date': 1,
                'search_default_groupby_analytic_account_id': 0,
                'search_default_groupby_type': 1,
            },
            'res_model': 'management.cost',
            'type': 'ir.actions.act_window',
            'target': 'main',
        }
