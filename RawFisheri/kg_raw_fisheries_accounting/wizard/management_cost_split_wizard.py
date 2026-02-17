# -*- coding: utf-8 -*-
import base64
from io import BytesIO

import xlwt


from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ManagementCostSplit(models.TransientModel):
    _name = 'management.cost.split.wizard'
    _description = 'management.cost.split.wizard'

    analytic_account_ids = fields.Many2many('account.analytic.account', string='Analytic Account')
    split_percent = fields.Float(string='Split Percentage')
    from_date = fields.Date(string='Date From', default=lambda self: fields.Date.context_today(self).replace(day=1))
    to_date = fields.Date(string='Date To', default=fields.Date.today)

    def default_get(self, fields):
        """ Listing all analytic accounts wth boolean show in report enabled """
        res = super(ManagementCostSplit, self).default_get(fields)
        analytic_accounts = self.env['account.analytic.account'].search(
            [('show_in_mc', '=', True)])
        res['analytic_account_ids'] = [(6, 0, analytic_accounts.ids)]
        return res

    def get_data(self):
        """ Function to get data for the report """
        for rec in self:
            value_list = []
            move_lines = self.env['account.move.line'].sudo().search(
                [('move_id.state', '=', 'posted'), ('move_id.invoice_date', '>=', rec.from_date),
                 ('move_id.invoice_date', '<=', rec.to_date)])
            aggregated_data = {}
            for move_line in move_lines:
                for analytic in move_line.analytic_line_ids:
                    if analytic.account_id.id in rec.analytic_account_ids.ids:
                        key = (analytic.date, analytic.account_id, move_line.account_id.account_type)

                        if key not in aggregated_data:
                            aggregated_data[key] = 0.0
                        aggregated_data[key] += move_line.price_total
            for (record_date, analytic_account_id, account_type), total_amount in aggregated_data.items():
                vals = {
                    'date': record_date,
                    'analytic_account_id': analytic_account_id.name,
                    'amount': total_amount,
                    'type': 'income' if account_type in ('income',
                                                         'other_income') else 'cor' if account_type == 'expense_direct_cost' else 'oin' if account_type == 'income_other' else 'dep' if account_type == 'expense_depreciation' else 'expense',
                }
                value_list.append(vals)
            return value_list

    def action_print_xlsx(self):
        """ Action to print the excel report with management cost split """
        value_list = self.get_data()
        if not value_list:
            raise ValidationError("There is no data in the selected time period!")

        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Management Cost')

        from_date = fields.Date.to_date(self.from_date).strftime('%d %B %Y')
        to_date = fields.Date.to_date(self.to_date).strftime('%d %B %Y')

        bold_font_large = xlwt.Font()
        bold_font_large.bold = True
        bold_font_large.height = 350

        bold_style_large = xlwt.XFStyle()
        bold_style_large.font = bold_font_large
        alignment_large = xlwt.Alignment()
        alignment_large.horz = xlwt.Alignment.HORZ_CENTER
        bold_style_large.alignment = alignment_large

        bold_font_small = xlwt.Font()
        bold_font_small.bold = True
        bold_font_small.height = 220

        bold_style_small = xlwt.XFStyle()
        bold_style_small.font = bold_font_small
        alignment_small = xlwt.Alignment()
        alignment_small.horz = xlwt.Alignment.HORZ_CENTER
        bold_style_small.alignment = alignment_small

        worksheet.write_merge(0, 1, 4, 8, 'MANAGEMENT COST SPLIT', bold_style_large)
        worksheet.write_merge(3, 3, 1, 3, f'From: {from_date}', bold_style_small)
        worksheet.write_merge(3, 3, 13, 15, f'To: {to_date}', bold_style_small)
        worksheet.write_merge(4, 4, 2, 5, "Type", bold_style_small)

        accounts = sorted(set(item['analytic_account_id'] for item in value_list))
        account_column_map = {account: 5 + idx * 2 for idx, account in enumerate(accounts)}

        for account, col in account_column_map.items():
            worksheet.write_merge(4, 4, col, col + 1, account, bold_style_small)

        types = ["Operating Income", "Cost of Revenue", "Other Income", "Expense", "Depreciation"]
        for row, t in enumerate(types, start=5):
            worksheet.write_merge(row, row, 1, 4, t, bold_style_small)

        data_dict = {}
        type_mapping = {
            'income': 'Operating Income',
            'cor': 'Cost of Revenue',
            'oin': 'Other Income',
            'expense': 'Expense',
            'dep': 'Depreciation'
        }

        for item in value_list:
            account = item['analytic_account_id']
            type_ = item['type']
            amount = item['amount']

            display_type = type_mapping.get(type_, type_)
            data_dict.setdefault(account, {}).setdefault(display_type, 0)
            data_dict[account][display_type] += amount

        for account, col in account_column_map.items():
            for row, t in enumerate(types, start=5):
                amount = data_dict.get(account, {}).get(t, 0)
                worksheet.write_merge(row, row, col, col + 1, amount)

        management_cost_account = next(
            (acc for acc in accounts if self.env['account.analytic.account'].search(
                [('name', '=', acc), ('management_cost', '=', True)])), None
        )
        if management_cost_account:
            management_total = sum(data_dict.get(management_cost_account, {}).values())
            split_percentage = self.split_percent / 100.0

            # Allocate management cost to other accounts
            management_allocation = {
                account: management_total * split_percentage for account in accounts if account != management_cost_account
            }

            # Add row for Management Cost Allocation
            row = len(types) + 5
            worksheet.write_merge(row, row, 1, 4, "Management Cost Allocation", bold_style_small)
            for account, col in account_column_map.items():
                allocated_amount = management_allocation.get(account, 0)
                worksheet.write_merge(row, row, col, col + 1, allocated_amount)

        output = BytesIO()
        workbook.save(output)
        output.seek(0)
        attachment = self.env['ir.attachment'].create({
            'name': 'Entries_Report.xls',
            'type': 'binary',
            'datas': base64.b64encode(output.getvalue()),
            'res_model': self._name,
            'res_id': self.id,
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
