from odoo import models, fields
import xlsxwriter
from io import BytesIO

class EstimationXlsxReport(models.AbstractModel):
    _name = 'report.kg_crm.report_estimation_xlsx'
    _description = 'Estimation Excel Report'

    def create_xlsx_report(self, docids, data=None):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        estimations = self.env['kg.crm.estimation'].browse(docids)
        self.generate_xlsx_report(workbook, data, estimations)
        workbook.close()
        output.seek(0)
        return output.getvalue(), 'xlsx'

    def generate_xlsx_report(self, workbook, data, estimations):
        for estimation in estimations:
            sheetname = estimation.name
            if not isinstance(sheetname, str):
                sheetname = str(sheetname)
            sheetname = sheetname[:31]

            sheet = workbook.add_worksheet(sheetname)
            bold = workbook.add_format({'bold': True})
            heading_format = workbook.add_format({'bold': True, 'font_size': 16, 'align': 'center', 'valign': 'vcenter'})
            subheading_format = workbook.add_format({'bold': True, 'font_size': 12, 'align': 'center', 'valign': 'vcenter'})
            date_format = workbook.add_format({'num_format': 'yyyy-mm-dd', 'align': 'left'})
            left_align_format = workbook.add_format({'align': 'left'})
            center_align_format = workbook.add_format({'align': 'center'})

            # Currency format
            currency_format = workbook.add_format({'num_format': '#,##0.00 $', 'align': 'left'})

            sheet.merge_range('A1:G1', 'Estimation Report', heading_format)
            sheet.merge_range('A2:G2', estimation.name, subheading_format)

            sheet.set_column('A:A', 20)
            sheet.set_column('B:B', 15)
            sheet.set_column('C:C', 30)
            sheet.set_column('D:D', 15)
            sheet.set_column('E:E', 15)
            sheet.set_column('F:F', 15)
            sheet.set_column('G:G', 20)

            headers = ['Customer', 'Date', 'Scope of Work', 'Total', 'Margin', 'Margin Amount', 'Proposal Cost']
            for col_num, header in enumerate(headers):
                sheet.write(3, col_num, header, bold)

            currency_symbol = estimation.currency_id.symbol or '$'

            # Add data rows
            sheet.write(4, 0, estimation.customer_id.name)
            sheet.write_datetime(4, 1, estimation.date, date_format)
            sheet.write(4, 2, estimation.scope_of_work, left_align_format)
            sheet.write(4, 3, f"{estimation.total:.2f} {currency_symbol}", left_align_format)
            sheet.write(4, 4, f"{estimation.margin:.2f}%", center_align_format)
            sheet.write(4, 5, f"{estimation.margin_amount:.2f} {currency_symbol}", left_align_format)
            sheet.write(4, 6, f"{estimation.proposal_cost:.2f} {currency_symbol}", left_align_format)

            line_headers = ['Item', 'Effort', 'Cost']
            row = 6
            for col_num, header in enumerate(line_headers):
                sheet.write(row, col_num, header, bold)

            sheet.set_column('A:A', 30)
            sheet.set_column('B:B', 15)
            sheet.set_column('C:C', 15)

            row += 1
            for line in estimation.estimation_line_ids:
                sheet.write(row, 0, line.item_id.name)
                sheet.write(row, 1, line.effort, left_align_format)
                sheet.write(row, 2, f"{line.cost:.2f} {currency_symbol}", left_align_format)
                row += 1

