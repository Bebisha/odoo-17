import base64
from base64 import encodebytes
from datetime import date, datetime, timedelta
from io import BytesIO

import xlsxwriter
import xlwt
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta

class BondsReportWizard(models.TransientModel):
    _name = 'bond.report.wizard'
    _description = 'Bonds Report Wizard'

    from_date = fields.Date(string="From")
    to_date = fields.Date(string="To")
    company_id = fields.Many2one('res.company',string='Company',required=True)
    year = fields.Char(string='Year',required=True)

    def bonds_report_button_xlsx(self):
        bonds = self.env['kg.bonds'].search([('company_id','=',self.company_id.id)])  # You may want to add domain filters here

        # Create workbook and worksheet
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Bonds Report')

        # Define styles for headers and data cells
        bold_style = xlwt.easyxf('font: bold on; align: horiz center;')
        data_style = xlwt.easyxf('align: horiz center;')

        # Define headers
        headers = [
            'Bond Name', 'ISIN', 'Company', 'Purchase Price', 'Settlement Date',
            'Maturity Date', 'Yield', 'Interest'
            # Add more headers as needed
        ]

        # Write headers to Excel
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, bold_style)

        # Write data rows
        row = 1
        for bond in bonds:
            if bond.settlement_date:
                data = [
                    bond.investment_id.name,
                    bond.ISIN_code,
                    bond.company_id.name,
                    bond.purchase_price,
                    bond.settlement_date.strftime('%Y-%m-%d'),
                    bond.maturity_date.strftime('%Y-%m-%d'),
                    bond.yield_val,
                    # bond.interest,
                    # Add more fields as needed
                ]

            for col, value in enumerate(data):
                worksheet.write(row, col, value, data_style)

            row += 1

        # Save workbook to BytesIO buffer
        output = BytesIO()
        workbook.save(output)
        output.seek(0)

        # Create an attachment record
        attachment = self.env['ir.attachment'].create({
            'name': 'Bonds_Report.xls',
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

