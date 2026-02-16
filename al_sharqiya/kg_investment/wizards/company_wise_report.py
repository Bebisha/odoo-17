from datetime import date, datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import xlwt
import base64
from io import BytesIO


class CompanywiseWizard(models.TransientModel):
    _name = 'companywise.wizard'
    _description = 'Company Wise Report Wizard'

    # year = fields.Char(string="Year")
    from_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")
    company_id = fields.Many2one('res.company', string='Company')
    investment_type = fields.Many2one('kg.investment.type', string='Investment Type')
    year = fields.Selection(selection='_list_all_years', string='From')

    def _list_all_years(self):
        current_year = date.today().year
        years = [(str(year), str(year)) for year in range(2019, current_year + 1)]
        return years

    def company_report_button(self,):
        for rec in self:
            output_format = rec._context.get('output_format','pdf')  # Get output_format from context, defaulting to 'pdf'

            inv_entry = self.env['kg.investment.entry'].search([])
            vals = []
            start_date = self.from_date
            end_date = self.to_date

            for inv in inv_entry:
                purchase_orders = inv.purchase_order_ids.filtered(lambda x:x.date and
                                                                  start_date <= x.date <= end_date and x.state == 'posted')
                sale_orders = inv.sale_order_ids.filtered(lambda x:x.date and
                                                          start_date <= x.date <= end_date and x.state == 'posted')

                total_purchased_qty = sum(purchase_order.no_of_shares for purchase_order in purchase_orders)
                total_sold_qty = sum(sale_order.no_of_shares for sale_order in sale_orders)

                purchase_total_cost = sum(purchase_order.no_of_shares * purchase_order.cost for purchase_order in purchase_orders)

                avg_cost = purchase_total_cost / total_purchased_qty if total_purchased_qty != 0 else 0.0

                sale_total_cost = sum(sale_order.no_of_shares * sale_order.cost for sale_order in sale_orders)

                sale_avg_cost = sale_total_cost / total_sold_qty if total_sold_qty != 0 else 0.0
                currency = self.company_id.currency_id
                exchange_rate = currency.rate

                purchase_share_value = total_purchased_qty * avg_cost * exchange_rate
                sale_share_value = total_sold_qty * sale_avg_cost * exchange_rate

                vals.append({
                    'investment_type': inv.investment_type.name,
                    'total_purchased_qty': total_purchased_qty,
                    'total_sold_qty': total_sold_qty,
                    'purchase_share_value': purchase_share_value,
                    'sale_share_value': sale_share_value,
                })

        data = {
            'values': vals,
            'company': self.company_id.name,
            'year': self.year,
            'from_date': self.from_date,
            'to_date': self.to_date,
        }

        if output_format == 'xlsx':
            workbook = xlwt.Workbook()
            worksheet = workbook.add_sheet('Company Wise Report')

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
            worksheet.write_merge(0, 1, 3, 7, 'Company wise Report', bold_style_large)

            headers = [
                'Investment Type',
                'Total Purchased Qty',
                'Total Sold Qty',
                'Purchase Share Value',
                'Sale Share Value'
            ]
            for col, header in enumerate(headers):
                worksheet.write_merge(3,4, col * 2+2 ,col*2+3, header, bold_style_small)

            # Write data rows
            row = 5
            for data_row in vals:
                worksheet.write_merge(row,row, 2,3, data_row['investment_type'])
                worksheet.write_merge(row,row, 4,5, data_row['total_purchased_qty'])
                worksheet.write_merge(row,row, 6,7, data_row['total_sold_qty'])
                worksheet.write_merge(row,row, 8,9, data_row['purchase_share_value'])
                worksheet.write_merge(row,row, 10,11, data_row['sale_share_value'])

                row += 1
            grand_total_purchased_qty = sum(data_row['total_purchased_qty'] for data_row in vals)
            grand_total_sold_qty = sum(data_row['total_sold_qty'] for data_row in vals)
            grand_total_purchase_share_value = sum(data_row['purchase_share_value'] for data_row in vals)
            grand_total_sale_share_value = sum(data_row['sale_share_value'] for data_row in vals)

            worksheet.write_merge(row, row, 2, 3, 'Grand Total', bold_style_small)
            worksheet.write_merge(row, row, 4, 5, grand_total_purchased_qty, bold_style_small)
            worksheet.write_merge(row, row, 6, 7, grand_total_sold_qty, bold_style_small)
            worksheet.write_merge(row, row, 8, 9, grand_total_purchase_share_value, bold_style_small)
            worksheet.write_merge(row, row, 10, 11, grand_total_sale_share_value, bold_style_small)

            # Close the workbook
            output = BytesIO()
            workbook.save(output)
            output.seek(0)
            attachment = self.env['ir.attachment'].create({
                'name': 'Company Wise Report.xls',
                'type': 'binary',
                'datas': base64.b64encode(output.getvalue()),
                'res_model': self._name,
                'res_id': self.id,
            })

            # Return an action to open the attachment
            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/{attachment.id}?download=true',
                'target': 'self',
            }

            # Return an action to open the attachment

        else:  # Default to PDF
            return self.env.ref('kg_investment.action_report_company_wise').with_context(
            landscape=True).report_action(self, data=data)
