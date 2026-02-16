from datetime import date, datetime, timedelta

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

import xlwt
import base64
from io import BytesIO
import calendar


class SaleSummaryWizard(models.TransientModel):
    _name = 'sale.summary.wizard'
    _description = 'Sale Summary Report Wizard'

    # from_year = fields.Char(string="From")
    range = fields.Integer(string="No of Years")
    from_date = fields.Date(string="From")
    to_date = fields.Date(string="To")
    company_id = fields.Many2one('res.company', string='Company')
    investment_type = fields.Many2one('kg.investment.type', string='Investment Type')
    report_type = fields.Selection(
        [('monthly', 'Monthly Report'), ('yearly', 'Yearly Report'),
         ], default="yearly", string='Report Type', required=True)
    from_year = fields.Selection(selection='_list_all_years',string='From')

    def _list_all_years(self):
        current_year = date.today().year
        years = [(str(year), str(year)) for year in range(2019, current_year + 1)]
        return years
    @api.constrains('from_date', 'to_date')
    def date_year_validation(self):
        """ Set validation error for dates """
        if self.report_type == 'monthly':
            for record in self:
                if record.from_date and record.to_date:
                    if record.from_date.year != record.to_date.year:
                        raise ValidationError('Both the From Date and To date must be within the same year.')

    def sale_summary_report_button(self):
        """ To print Pdf report"""
        if self.report_type == 'yearly':
            start_year = int(self.from_year)
            end_year = start_year + self.range
            if start_year > date.today().year:
                raise ValidationError(_('No records found'))
            sale_orders = self.env['kg.sale.order'].search(
                [('state', '=', 'posted'), ('investment_type_id', '=', self.investment_type.id),('company_id','=',self.company_id.id)])
            investments = sale_orders.mapped('investment_id').sorted(
                key=lambda x: x.name)
            year_wise = {}
            year_totals = {year: {'no_shares': 0, 'cost': 0, 'share_value': 0} for year in
                           range(start_year, end_year + 1)}

            for investment in investments:
                investment_data = {}
                for year in range(start_year, end_year + 1):
                    sales = sale_orders.filtered(lambda p: p.date.year == year and p.investment_id == investment)

                    no_shares = sum(p.no_of_shares for p in sales)
                    date_start = date(year, 1, 1)
                    date_end = date(year, 12, 31)
                    cost = 0.0
                    market = self.env['market.rate.updation'].search([
                        ('investment_type_id', '=', investment.investment_type.id),
                        ('date', '>=', date_start),
                        ('date', '<=', date_end),
                    ], limit=1)
                    if market:
                        for market_line in market.market_rate_line_id:
                            if market_line.investment_id.name == investment.name:
                                market_rate = market_line.market_rate
                                cost = market_rate
                                break  # Found relevant market rate, exit loop
                    else:
                        cost = 0.0  # Default cost if market rate not found
                    share_value = cost * no_shares
                    investment_data[year] = {
                        'no_shares': no_shares,
                        'cost': cost,
                        'share_value': share_value
                    }
                    year_totals[year]['no_shares'] += no_shares
                    year_totals[year]['cost'] += cost
                    year_totals[year]['share_value'] += share_value

                year_wise[investment.name] = investment_data

            data = {
                'company': self.company_id.name,
                'investment_type': self.investment_type.name,
                'range': self.range,
                'start_year': start_year,
                'end_year': end_year,
                'year_wise': year_wise,
                'year_totals': year_totals,
                'investment': investments,
                'report_type': self.report_type
            }
        else:
            data = self.get_monthly_records()
        return self.env.ref('kg_investment.action_report_sale_summary').with_context(
            landscape=True).report_action(self, data=data)

    def get_monthly_records(self):
        """ To get the data month-wise """
        from_date = self.from_date
        to_date = self.to_date
        if from_date > to_date:
            raise ValidationError(_('Invalid date range'))
        sale_orders = self.env['kg.sale.order'].search([
            ('state', '=', 'posted'),
            ('investment_type_id', '=', self.investment_type.id),
            ('date', '>=', from_date),
            ('date', '<=', to_date),
            ('company_id', '=', self.company_id.id),
        ])
        investments = sale_orders.mapped('investment_id').sorted(key=lambda x: x.name)
        month_wise = {}
        months_list = []
        current_date = from_date
        while current_date <= to_date:
            month = current_date.month
            year = current_date.year
            month_name_str = calendar.month_abbr[month]
            last_day = calendar.monthrange(year, month)[1]
            end_of_month = current_date.replace(day=last_day)
            months_list.append(month_name_str)
            for investment in investments:
                if investment.name not in month_wise:
                    month_wise[investment.name] = {}
                if month_name_str not in month_wise[investment.name]:
                    month_wise[investment.name][month_name_str] = {
                        'no_shares': 0,
                        'cost': 0.0,
                        'share_value': 0.0
                    }
                month_purchases = sale_orders.filtered(
                    lambda p: p.date.month == month and p.date.year == year and p.investment_id == investment
                )
                no_shares = sum(p.no_of_shares for p in month_purchases)
                cost = 0.0
                market = self.env['market.rate.updation'].search([
                    ('investment_type_id', '=', investment.investment_type.id),
                    ('date', '>=', current_date.replace(day=1)),
                    ('date', '<=', end_of_month),
                ], limit=1)
                if market:
                    for market_line in market.market_rate_line_id:
                        if market_line.investment_id.name == investment.name:
                            market_rate = market_line.market_rate
                            cost = market_rate
                            break
                else:
                    cost = 0.0
                share_value = cost * no_shares
                month_wise[investment.name][month_name_str] = {
                    'no_shares': no_shares,
                    'cost': cost,
                    'share_value': "{:.6f}".format(share_value),
                }
            current_date += relativedelta(months=1)
        month_totals = {}
        for month_name_str in months_list:
            month_totals[month_name_str] = {'no_shares': 0, 'cost': 0, 'share_value': 0}
            for investment in investments:
                if month_name_str in month_wise.get(investment.name, {}):
                    month_totals[month_name_str]['no_shares'] += month_wise[investment.name][month_name_str][
                        'no_shares']
                    month_totals[month_name_str]['cost'] += month_wise[investment.name][month_name_str]['cost']
                    month_totals[month_name_str]['share_value'] += round(
                        float(month_wise[investment.name][month_name_str]['share_value']), 6)
        data = {
            'company': self.company_id.name,
            'investment_type': self.investment_type.name,
            'range': self.range,
            'start_year': calendar.month_name[from_date.month],
            'end_year': calendar.month_name[to_date.month],
            'year_wise': month_wise,
            'months_list': months_list,
            'month_totals': month_totals,
            'investment': investments,
            'report_type': self.report_type
        }
        return data

    def sale_summary_report_button_xlsx(self):
        if self.report_type == 'yearly':
            start_year = int(self.from_year)
            end_year = start_year + self.range
            if start_year > date.today().year:
                raise ValidationError(_('No records found'))
            sale_orders = self.env['kg.sale.order'].search(
                [('state', '=', 'posted'), ('investment_type_id', '=', self.investment_type.id),('company_id','=',self.company_id.id)])
            investments = sale_orders.mapped('investment_id').sorted(
                key=lambda x: x.name)
            year_wise = {}
            year_totals = {year: {'no_shares': 0, 'cost': 0, 'share_value': 0} for year in range(start_year, end_year + 1)}

            for investment in investments:
                investment_data = {}
                for year in range(start_year, end_year + 1):
                    sales = sale_orders.filtered(lambda p: p.date.year == year and p.investment_id == investment)
                    no_shares = sum(p.no_of_shares for p in sales)
                    date_start = date(year, 1, 1)
                    date_end = date(year, 12, 31)
                    cost = 0.0
                    market = self.env['market.rate.updation'].search([
                        ('investment_type_id', '=', investment.investment_type.id),
                        ('date', '>=', date_start),
                        ('date', '<=', date_end),
                    ], limit=1)

                    if market:
                        for market_line in market.market_rate_line_id:
                            if market_line.investment_id.name == investment.name:
                                market_rate = market_line.market_rate
                                cost = market_rate
                                break  # Found relevant market rate, exit loop
                    else:
                        cost = 0.0  # Default cost if market rate not found
                    share_value = cost * no_shares
                    investment_data[year] = {
                        'no_shares': no_shares,
                        'cost': cost,
                        'share_value': share_value
                    }
                    year_totals[year]['no_shares'] += no_shares
                    year_totals[year]['cost'] += cost
                    year_totals[year]['share_value'] += share_value

                year_wise[investment.name] = investment_data

        # Create workbook
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Sales Summary')

        # Define bold font style for headers with increased font size
        bold_font_large = xlwt.Font()
        bold_font_large.bold = True
        bold_font_large.height = 350  # Larger font size for Purchase Summary heading

        bold_style_large = xlwt.XFStyle()
        bold_style_large.font = bold_font_large
        alignment_large = xlwt.Alignment()
        alignment_large.horz = xlwt.Alignment.HORZ_CENTER  # Horizontal center alignment
        bold_style_large.alignment = alignment_large

        # Define style with bold font and centered alignment for other headers (smaller font size)
        bold_font_small = xlwt.Font()
        bold_font_small.bold = True
        bold_font_small.height = 220  # Smaller font size for other headers

        bold_style_small = xlwt.XFStyle()
        bold_style_small.font = bold_font_small
        alignment_small = xlwt.Alignment()
        alignment_small.horz = xlwt.Alignment.HORZ_CENTER  # Horizontal center alignment
        bold_style_small.alignment = alignment_small

        # Merge cells and write Purchase Summary heading
        worksheet.write_merge(0, 1, 4, 8, 'Yearly Sales/ Sell Analysis', bold_style_large)
        if self.report_type == 'yearly':
            for i, year in enumerate(range(start_year, end_year + 1)):
                col = i * 3 + 1
                worksheet.write_merge(3, 4, col, col + 2, str(year), bold_style_small)
                worksheet.write_merge(5, 6, col, col, 'No of\nShares', bold_style_small)
                worksheet.write_merge(5, 6, col + 1, col + 1, 'Share\nRate', bold_style_small)
                worksheet.write_merge(5, 6, col + 2, col + 2, 'Share\nValue', bold_style_small)
            row = 7
            for investment_name, data in year_wise.items():
                worksheet.write(row, 0, investment_name)
                for year in range(start_year, end_year + 1):
                    row_data = data.get(year, {})
                    col = (year - start_year) * 3 + 1
                    worksheet.write(row, col, row_data.get('no_shares', ''), xlwt.Style.default_style)
                    worksheet.write(row, col + 1, row_data.get('cost', ''), xlwt.Style.default_style)
                    worksheet.write(row, col + 2, row_data.get('share_value', ''), xlwt.Style.default_style)
                row += 1
            grand_total_row = row
            worksheet.write(grand_total_row, 0, 'Total', bold_style_small)
            for i, year in enumerate(range(start_year, end_year + 1)):
                col = i * 3 + 1
                worksheet.write(grand_total_row, col, year_totals[year]['no_shares'], bold_style_small)
                worksheet.write(grand_total_row, col + 1, year_totals[year]['cost'], bold_style_small)
                worksheet.write(grand_total_row, col + 2, year_totals[year]['share_value'], bold_style_small)
        else:
            month_wise = self.get_monthly_records()
            for i, month in enumerate(month_wise['months_list']):
                col = i * 3 + 1
                worksheet.write_merge(3, 4, col, col + 2, month, bold_style_small)
                worksheet.write_merge(5, 6, col, col, 'No of\nShares', bold_style_small)
                worksheet.write_merge(5, 6, col + 1, col + 1, 'Share\nRate', bold_style_small)
                worksheet.write_merge(5, 6, col + 2, col + 2, 'Share\nValue', bold_style_small)
            row = 7
            for investment_name, monthly_data in month_wise['year_wise'].items():
                worksheet.write(row, 0, investment_name)
                for month_index, (month, data) in enumerate(monthly_data.items()):
                    col = month_index * 3 + 1
                    worksheet.write(row, col, data.get('no_shares', ''), xlwt.Style.default_style)
                    worksheet.write(row, col + 1, data.get('cost', ''), xlwt.Style.default_style)
                    worksheet.write(row, col + 2, data.get('share_value', ''), xlwt.Style.default_style)
                row += 1
            grand_total_row = row
            worksheet.write(grand_total_row, 0, 'Total', bold_style_small)

            for month_index, month in enumerate(month_wise['months_list']):
                col = month_index * 3 + 1
                worksheet.write(grand_total_row, col, month_wise['month_totals'][month]['no_shares'], bold_style_small)
                worksheet.write(grand_total_row, col + 1, month_wise['month_totals'][month]['cost'], bold_style_small)
                worksheet.write(grand_total_row, col + 2, month_wise['month_totals'][month]['share_value'],
                                bold_style_small)
        output = BytesIO()
        workbook.save(output)
        output.seek(0)
        attachment = self.env['ir.attachment'].create({
            'name': 'Sale_Summary_Report.xls',
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
