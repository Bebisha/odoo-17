# -*- coding: utf-8 -*-

from datetime import timedelta, date

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _


class ManagementCostWizard(models.TransientModel):
    """ To view the management cost monthly report """
    _name = 'management.cost.monthly.wizard'
    _description = 'management.cost.monthly.wizard'

    analytic_account_ids = fields.Many2many('account.analytic.account', string='Analytic Account')

    def default_get(self, fields):
        """ Listing all analytic accounts wth boolean show in report enabled """
        res = super(ManagementCostWizard, self).default_get(fields)
        analytic_accounts = self.env['account.analytic.account'].search(
            [('show_in_mc', '=', True)])
        res['analytic_account_ids'] = [(6, 0, analytic_accounts.ids)]
        return res

    def load_analytic_account_details(self):
        """ Function to load data in the pivot view, aggregated month-wise """

        analytic_lines = self.env['account.analytic.line'].sudo().search([('account_id', 'in', self.analytic_account_ids.ids)])

        aggregated_data = {}
        for line in analytic_lines:
            month_start_date = line.date.replace(day=1)
            key = (month_start_date, line.account_id.id, line.move_line_id.account_id.account_type)
            if key not in aggregated_data:
                aggregated_data[key] = 0.0
            aggregated_data[key] += line.amount

        domain_list = []
        for (month_start_date, analytic_account_id, account_type), total_amount in aggregated_data.items():
            report_record = self.env['management.cost.monthly'].sudo().create({
                'date': month_start_date,
                'analytic_account_id': analytic_account_id,
                'amount': total_amount,
                'type': 'income' if account_type in ('income',
                                                     'other_income') else 'cor' if account_type == 'expense_direct_cost' else 'oin' if account_type == 'income_other' else 'dep' if account_type == 'expense_depreciation' else 'expense',
            })
            domain_list.append(report_record.id)

        return {
            'name': _('Management Cost Monthly'),
            'view_type': 'form',
            'view_mode': 'pivot,tree',
            'domain': [('id', 'in', domain_list)],
            'context': {
                'search_default_groupby_date': 1,
                'search_default_groupby_analytic_account_id': 0,
            },
            'res_model': 'management.cost.monthly',
            'type': 'ir.actions.act_window',
            'target': 'main',
        }