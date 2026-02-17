# -*- coding: utf-8 -*-

from datetime import timedelta, date

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _


class ManagementCostWizard(models.TransientModel):
    """ To view the management cost report """
    _name = 'management.cost.wizard'
    _description = 'management.cost.wizard'

    analytic_account_ids = fields.Many2many('account.analytic.account', string='Analytic Account')

    def default_get(self, fields):
        """ Listing all analytic accounts wth boolean show in report enabled """
        res = super(ManagementCostWizard, self).default_get(fields)
        analytic_accounts = self.env['account.analytic.account'].search(
            [('show_in_mc', '=', True)])
        res['analytic_account_ids'] = [(6, 0, analytic_accounts.ids)]
        return res

    def load_analytic_account_details(self):
        """ Function to load data in the pivot view """
        today = date.today()
        first_day = today.replace(day=1)
        last_day = first_day + relativedelta(months=1) - timedelta(days=1)

        analytic_lines = self.env['account.analytic.line'].sudo().search([
            ('id', 'in', self.analytic_account_ids.ids),
            ('date', '>=', first_day),
            ('date', '<=', last_day)
        ])

        move_lines = self.env['account.move.line'].sudo().search(
            [('move_id.state', '=', 'posted'), ('move_id.invoice_date', '>=', first_day),
             ('move_id.invoice_date', '<=', last_day)])
        aggregated_data = {}

        for move_line in move_lines:
            for analytic in move_line.analytic_line_ids:
                if analytic.account_id.id in self.analytic_account_ids.ids:
                    key = (analytic.date, analytic.account_id.id, move_line.account_id.account_type)

                    if key not in aggregated_data:
                        aggregated_data[key] = 0.0
                    aggregated_data[key] += move_line.price_total
        # aggregated_data = {}
        # for line in analytic_lines:
        #     key = (line.date, line.account_id.id, line.move_line_id.account_id.account_type)
        #     if key not in aggregated_data:
        #         aggregated_data[key] = 0.0
        #     aggregated_data[key] += line.amount

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
