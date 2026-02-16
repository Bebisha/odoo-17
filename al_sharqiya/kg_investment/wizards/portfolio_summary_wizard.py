import base64
from base64 import encodebytes
from datetime import date, datetime, timedelta
from io import BytesIO

import xlsxwriter
import xlwt
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta

class PortfolioSummaryWizard(models.TransientModel):
    _name = 'portfolio.summary.wizard'
    _description = 'Purchase Summary Report Wizard'

    from_date = fields.Date(string="From")
    to_date = fields.Date(string="To")
    company_id = fields.Many2one('res.company',string='Company',required=True)
    # year = fields.Char(string='Year',required=True)
    investment_type = fields.Many2one('kg.investment.type',string='Investment Type')
    month = fields.Selection(
        selection=[
            ('january', 'January'),
            ('february', 'February'),
            ('march', 'March'),
            ('april', 'April'),
            ('may', 'May'),
            ('june', 'June'),
            ('july', 'July'),
            ('august', 'August'),
            ('september', 'September'),
            ('october', 'October'),
            ('november', 'November'),
            ('december', 'December')
        ],
        string='Month',
        required=True
    )
    year = fields.Selection(selection='_list_all_years', string='From')

    def _list_all_years(self):
        current_year = date.today().year
        years = [(str(year), str(year)) for year in range(2019, current_year + 1)]
        return years

    def portfolio_summary_report_button(self):
        if self.from_date > self.to_date:
            raise ValidationError(_('Invalid date range'))

        start_date = self.from_date  # Directly use self.from_date

        date_start = datetime.strptime(f"{self.year}-01-01", "%Y-%m-%d")
        date_end = datetime.strptime(f"{self.year}-12-31", "%Y-%m-%d")


        # Calculate previous year dates
        current_year = int(self.year)  # Convert self.year to integer
        previous_year = current_year - 1
        prev_date_start = datetime.strptime(f"{previous_year}-01-01", "%Y-%m-%d")
        prev_date_end = datetime.strptime(f"{previous_year}-12-31", "%Y-%m-%d")

        # prev_date_start = datetime.strptime(f"{previous_year}-{self.month}-01", "%Y-%m-%d")
        # prev_date_end = (prev_date_start + relativedelta(months=1, days=-1)).date()

        inv_entry = self.env['kg.investment.entry'].search([])  # Assuming all entries are relevant

        vals = []
        month = self.month.capitalize()[:3]
        company_id= self.company_id
        for inv in inv_entry:
            purchase_orders = inv.purchase_order_ids.filtered(lambda x:
                                                              x.date and
                                                              x.date.strftime('%B')[:3].capitalize() == month and x.state == 'posted' and x.company_id == company_id)
            sale_orders = inv.sale_order_ids.filtered(lambda x:
                                                      x.date and
                                                      x.date.strftime('%B')[:3].capitalize() == month and x.state == 'posted' and x.company_id == company_id)

            total_purchased_qty = sum(purchase_order.no_of_shares for purchase_order in purchase_orders)
            total_sold_qty = sum(sale_order.no_of_shares for sale_order in sale_orders)

            total_qty = total_purchased_qty - total_sold_qty

            if total_qty > 0:  # Only include entries with positive total quantity
                total_cost = sum(
                    purchase_order.no_of_shares * purchase_order.cost for purchase_order in purchase_orders)
                avg_cost = total_cost / total_qty

                currency = self.company_id.currency_id
                exchange_rate = currency.rate
                share_value = total_qty * avg_cost * exchange_rate

                # Fetch current year's market rate
                market = self.env['market.rate.updation'].search([
                    ('investment_type_id', '=', inv.investment_type.id),
                    ('date', '>=', date_start.date()),
                    ('date', '<=', date_end.date())
                ], limit=1)

                market_rate = 0.0
                if market:
                    market_rate_line = market.market_rate_line_id.filtered(lambda x: x.investment_id.name == inv.name)
                    if market_rate_line:
                        market_rate = market_rate_line.market_rate
                else:
                    market_rate = inv.face_value


                # Fetch previous year's market rate
                previous_market_value = 0.0
                prev_market = self.env['market.rate.updation'].search([
                    ('investment_type_id', '=', inv.investment_type.id),
                    ('date', '>=', prev_date_start.date()),
                    ('date', '<=', prev_date_end.date())
                ], limit=1)
                gain_loss=0.0
                market_value =0.0

                if prev_market:
                    prev_market_rate_line = prev_market.market_rate_line_id.filtered(
                        lambda x: x.investment_id.name == inv.name)
                    if prev_market_rate_line:
                        previous_market_value = prev_market_rate_line.market_rate * prev_market_rate_line.available_shares * exchange_rate

                # Calculate market value for current year
                market_value = market_rate * total_qty * exchange_rate
                gain_loss = previous_market_value -market_value
                purchase_exchanges = set(
                    purchase_order.exchange_id.name for purchase_order in purchase_orders if purchase_order.exchange_id)
                sale_exchanges = set(
                    sale_order.exchange_id.name for sale_order in sale_orders if sale_order.exchange_id)

                # Combine exchange names and choose a representative (if needed)
                combined_exchanges = purchase_exchanges.union(sale_exchanges)
                market_name = ', '.join(combined_exchanges) if combined_exchanges else 'N/A'
                print("market_name",market_name)

                vals.append({
                    'investment_type': self.investment_type.name,
                    'investment_name': inv.name,
                    'currency': currency.name,
                    'exchange_rate': "{:.6f}".format(exchange_rate),
                    'shares': total_qty,
                    'market':market_name,
                    'year': self.year,
                    'month': self.month.capitalize(),
                    'avg_rate': "{:.6f}".format(avg_cost),
                    'share_value': "{:.6f}".format(share_value),
                    'market_rate': "{:.6f}".format(market_rate) ,
                    'market_value': "{:.6f}".format(market_value),
                    'previous_market_value': "{:.6f}".format(previous_market_value),
                    'gain_loss': "{:.6f}".format(gain_loss),
                })

        data = {
            'values': vals,
            'company': self.company_id.name,
            'year': self.year,
            'month': month,
        }

        return self.env.ref('kg_investment.action_report_portfolio_summary').with_context(
            landscape=True).report_action(self, data=data)

    # def portfolio_summary_report_button_xlsx(self):
    #     if self.from_date > self.to_date:
    #         raise ValidationError(_('Invalid date range'))
    #
    #     start_date = self.from_date
    #     # end_date = self.to_date + relativedelta(day=31)
    #
    #     date_start = datetime.strptime(f"{self.year}-01-01", "%Y-%m-%d")
    #     date_end = datetime.strptime(f"{self.year}-12-31", "%Y-%m-%d")
    #
    #     # if start_date > date.today():
    #     #     raise ValidationError(_('No records found'))
    #
    #     inv_entry = self.env['kg.investment.entry'].search([])
    #
        # # Create workbook
        # workbook = xlwt.Workbook()
        # worksheet = workbook.add_sheet('Portfolio Summary')
        #
        # # Define bold font style
        # bold_font_large = xlwt.Font()
        # bold_font_large.bold = True
        # bold_font_large.height = 400  # Font size (height) in 1/20th of a point. For example, 300 is equivalent to 15pt font size.
        #
        # # Define style with bold font for Portfolio Summary heading
        # bold_style_large = xlwt.XFStyle()
        # bold_style_large.font = bold_font_large
        # bold_style_large = xlwt.XFStyle()
        # bold_style_large.font = bold_font_large
        # # Center alignment for Portfolio Summary heading
        # alignment_large = xlwt.Alignment()
        # alignment_large.horz = xlwt.Alignment.HORZ_CENTER
        # bold_style_large.alignment = alignment_large
        # # Merge cells E1 to F1 and set the heading
        # worksheet.write_merge(0, 1, 4, 7, 'Portfolio Summary', bold_style_large)
        #
        # # Define bold font style for headers
        # bold_font_small = xlwt.Font()
        # bold_font_small.bold = True
        # bold_font_small.height = 250  # Smaller font size for headers
        #
        # # Define style with bold font for headers
        # bold_style_small = xlwt.XFStyle()
        # bold_style_small.font = bold_font_small
        #
        # alignment = xlwt.Alignment()
        # alignment.horz = xlwt.Alignment.HORZ_CENTER
        # bold_style_small.alignment = alignment
        # header_style = xlwt.easyxf('pattern: pattern solid, fore_colour gray25; font: bold on;')
        # # Headers
        # headers = ['Investment Name', 'Currency', 'Exchange Rate', 'Shares',
        #            'Avg Rate', 'Share Value', 'Market Rate', 'Market Value', 'Year', 'Month']
        # for col, header in enumerate(headers):
        #     worksheet.write_merge(3, 5, col * 2, col * 2 + 1, header, bold_style_small)
        #     worksheet.row(3).set_style(header_style)  # Apply header row style
    #
    #     row = 6
    #     month = self.month.capitalize()[:3]
    #     for inv in inv_entry:
    #         purchase_orders = inv.purchase_order_ids.filtered(lambda x:
    #                                                           x.date and
    #                                                           x.date.strftime('%B')[:3].capitalize() == month)
    #         sale_orders = inv.sale_order_ids.filtered(lambda x:
    #                                                   x.date and
    #                                                   x.date.strftime('%B')[:3].capitalize() == month)
    #
    #         total_purchased_qty = sum(purchase_order.no_of_shares for purchase_order in purchase_orders)
    #         total_sold_qty = sum(sale_order.no_of_shares for sale_order in sale_orders)
    #
    #         total_qty = total_purchased_qty - total_sold_qty
    #
    #         if total_qty > 0:
    #             total_cost = sum(
    #                 purchase_order.no_of_shares * purchase_order.cost for purchase_order in purchase_orders)
    #             avg_cost = total_cost / total_qty
    #
    #             currency = inv.currency_id
    #             exchange_rate = inv.currency_id.rate
    #             share_value = total_qty * avg_cost * exchange_rate
    #
    #             market = self.env['market.rate.updation'].search(
    #                 [('investment_type_id', '=', inv.investment_type.id), ('date', '>=', date_start),
    #                  ('date', '<=', date_end)],
    #                 limit=1)
    #             market_rate = 0.0
    #             for market_line in market.market_rate_line_id:
    #                 if market_line.investment_id.name == inv.name:
    #                     market_rate = market_line.market_rate
    #                 else:
    #                     market_rate = 0.0
    #
    #             market_value = market_rate * total_qty * exchange_rate
    #             value_style = xlwt.XFStyle()
    #             alignment_value = xlwt.Alignment()
    #             alignment_value.horz = xlwt.Alignment.HORZ_CENTER
    #             value_style.alignment = alignment_value
    #             # Write data to Excel
    #             data = [inv.name, currency.name, "{:.6f}".format(exchange_rate), total_qty,
    #                     "{:.6f}".format(avg_cost), "{:.6f}".format(share_value),
    #                     "{:.6f}".format(market_rate), "{:.6f}".format(market_value),
    #                     self.year, month]
    #
    #             for col, value in enumerate(data):
    #                 worksheet.write_merge(row, row, col * 2, col * 2 + 1, value,value_style)
    #
    #             row += 1
    #
    #     # Save the workbook to a BytesIO buffer
    #     output = BytesIO()
    #     workbook.save(output)
    #     output.seek(0)
    #
    #     # Create an attachment record
    #     attachment = self.env['ir.attachment'].create({
    #         'name': 'Portfolio_Summary_Report.xls',
    #         'type': 'binary',
    #         'datas': base64.b64encode(output.getvalue()),
    #         'res_model': self._name,
    #         'res_id': self.id,
    #     })
    #
    #     # Return an action to open the attachment
    #     return {
    #         'type': 'ir.actions.act_url',
    #         'url': f'/web/content/{attachment.id}?download=true',
    #         'target': 'self',
    #     }

    def portfolio_summary_report_button_xlsx(self):
        if self.from_date > self.to_date:
            raise ValidationError(_('Invalid date range'))

        start_date = self.from_date
        date_start = datetime.strptime(f"{self.year}-01-01", "%Y-%m-%d")
        date_end = datetime.strptime(f"{self.year}-12-31", "%Y-%m-%d")

        current_year = int(self.year)
        previous_year = current_year - 1
        prev_date_start = datetime.strptime(f"{previous_year}-01-01", "%Y-%m-%d")
        prev_date_end = datetime.strptime(f"{previous_year}-12-31", "%Y-%m-%d")

        inv_entry = self.env['kg.investment.entry'].search([])

        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Portfolio Summary')

        # Define formats
        title_format = workbook.add_format(
            {'bold': True, 'font_size': 16, 'align': 'center', 'valign': 'vcenter', 'border': 1})
        bold_format = workbook.add_format({'bold': True, 'align': 'center', 'border': 1})
        center_format = workbook.add_format({'align': 'center', 'border': 1})
        number_format = workbook.add_format({'num_format': '#,##0.00', 'border': 1})

        # Add title
        worksheet.merge_range('A1:L1', 'Portfolio Summary', title_format)

        # Define headers
        headers = [
            'Investment Name', 'Currency', 'Exchange Rate',
            'Shares', 'Average Rate', 'Share Value','Market',
            'Market Rate', 'Market Value', 'Previous Market Value', 'Gain/Loss', 'Month', 'Year'
        ]

        # Write headers
        for col, header in enumerate(headers):
            worksheet.write(2, col, header, bold_format)

        month = self.month.capitalize()[:3]
        company_id = self.company_id
        row = 3

        for inv in inv_entry:
            purchase_orders = inv.purchase_order_ids.filtered(lambda x:
                                                              x.date and
                                                              x.date.strftime('%B')[
                                                              :3].capitalize() == month and x.state == 'posted' and x.company_id == company_id)
            sale_orders = inv.sale_order_ids.filtered(lambda x:
                                                      x.date and
                                                      x.date.strftime('%B')[
                                                      :3].capitalize() == month and x.state == 'posted' and x.company_id == company_id)

            total_purchased_qty = sum(purchase_order.no_of_shares for purchase_order in purchase_orders)
            total_sold_qty = sum(sale_order.no_of_shares for sale_order in sale_orders)

            total_qty = total_purchased_qty - total_sold_qty

            if total_qty > 0:
                total_cost = sum(
                    purchase_order.no_of_shares * purchase_order.cost for purchase_order in purchase_orders)
                avg_cost = total_cost / total_qty

                currency = self.company_id.currency_id
                exchange_rate = currency.rate
                share_value = total_qty * avg_cost * exchange_rate


                market = self.env['market.rate.updation'].search([
                    ('investment_type_id', '=', inv.investment_type.id),
                    ('date', '>=', date_start.date()),
                    ('date', '<=', date_end.date())
                ], limit=1)

                market_rate = 0.0
                if market:
                    market_rate_line = market.market_rate_line_id.filtered(lambda x: x.investment_id.name == inv.name)
                    if market_rate_line:
                        market_rate = market_rate_line.market_rate
                else:
                    market_rate = inv.face_value

                previous_market_value = 0.0
                prev_market = self.env['market.rate.updation'].search([
                    ('investment_type_id', '=', inv.investment_type.id),
                    ('date', '>=', prev_date_start.date()),
                    ('date', '<=', prev_date_end.date())
                ], limit=1)

                gain_loss = 0.0
                market_value = 0.0

                if prev_market:
                    prev_market_rate_line = prev_market.market_rate_line_id.filtered(
                        lambda x: x.investment_id.name == inv.name)
                    if prev_market_rate_line:
                        previous_market_value = prev_market_rate_line.market_rate * prev_market_rate_line.available_shares * exchange_rate

                market_value = market_rate * total_qty * exchange_rate
                gain_loss = previous_market_value - market_value

                purchase_exchanges = set(
                    purchase_order.exchange_id.name for purchase_order in purchase_orders if purchase_order.exchange_id)
                sale_exchanges = set(
                    sale_order.exchange_id.name for sale_order in sale_orders if sale_order.exchange_id)

                # Combine exchange names and choose a representative (if needed)
                combined_exchanges = purchase_exchanges.union(sale_exchanges)
                market_name = ', '.join(combined_exchanges) if combined_exchanges else 'N/A'

                worksheet.write(row, 0, inv.name, center_format)
                worksheet.write(row, 1, currency.name, center_format)
                worksheet.write(row, 2, exchange_rate, number_format)
                worksheet.write(row, 3, total_qty, center_format)
                worksheet.write(row, 4, avg_cost, number_format)
                worksheet.write(row, 5, share_value, number_format)
                worksheet.write(row, 6, market_name, center_format)
                worksheet.write(row, 7, market_rate, number_format)
                worksheet.write(row, 8, market_value, number_format)
                worksheet.write(row, 9, previous_market_value, number_format)
                worksheet.write(row, 10, gain_loss, number_format)
                worksheet.write(row, 11, self.month.capitalize(), center_format)
                worksheet.write(row, 12, self.year, center_format)

                row += 1

        workbook.close()
        output.seek(0)

        attachment_id = self.env['ir.attachment'].create({
            'name': f'Portfolio_Summary_{self.year}_{month}.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(output.getvalue()),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment_id.id}?download=true',
            'target': 'new'
        }