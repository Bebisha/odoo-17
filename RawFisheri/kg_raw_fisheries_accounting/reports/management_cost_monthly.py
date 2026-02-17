# -*- coding: utf-8 -*-

from datetime import timedelta, date

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _

class ManagementCost(models.Model):
    """ To view the management cost monthly comparison report """
    _name = 'management.cost.monthly'
    _description = 'management.cost.monthly'

    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    analytic_account_line_id = fields.Many2one('account.analytic.line', string='Analytic Account Line')
    date = fields.Date(string='Date')
    amount = fields.Float(string='Amount')
    type = fields.Selection(
        [('income', 'Income'), ('expense', 'Expense'), ('cor', 'Cost Of Revenue'), ('oin', 'Other Income'),
         ('dep', 'Depreciation')], string='Type',
        store=True)

    def load_analytic_account_details(self):
        """ Function to load data in the pivot view, aggregated month-wise """

        # Fetch all analytic lines
        analytic_lines = self.env['account.analytic.line'].sudo().search([('account_id.show_in_mc', '=', True)])

        aggregated_data = {}
        for line in analytic_lines:
            # Group by month and year of the date and analytic account
            month_start_date = line.date.replace(day=1)  # Start of the month
            key = (month_start_date, line.account_id.id)
            if key not in aggregated_data:
                aggregated_data[key] = 0.0
            aggregated_data[key] += line.amount

        # Create or update management.cost records
        domain_list = []
        for (month_start_date, analytic_account_id), total_amount in aggregated_data.items():
            report_record = self.env['management.cost.monthly'].sudo().create({
                'date': month_start_date,
                'analytic_account_id': analytic_account_id,
                'amount': total_amount,
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
