from odoo import models, fields, _
from odoo.exceptions import ValidationError
from base64 import encodebytes
from datetime import datetime, timedelta
from io import BytesIO
from odoo.exceptions import ValidationError, UserError
from odoo.tools.safe_eval import json

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class DayBookReportWizard(models.TransientModel):
    _name = "day.book.report.wizard"
    _description = "Day Book Report Wizard"

    name = fields.Char(string="Reference")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company)
    fileout = fields.Binary('File', readonly=True)
    fileout_filename = fields.Char('Filename', readonly=True)
    def button_day_book_report(self):
        if self.start_date > self.end_date:
            raise ValidationError(_('Start Date must be less than End Date'))

        vals = []
        aml_ids = self.env['account.move.line'].search([
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date),
            ('parent_state', '=', 'posted'),
            ('company_id', '=', self.company_id.id)
        ], order='date asc')

        journal_ids = list(set(aml_ids.mapped('journal_id.code')))
        journal_code = ', '.join(journal_ids)

        total_debit = 0.00
        total_credit = 0.00

        for line in aml_ids:
            total_debit += line.debit
            total_credit += line.credit

            line_vals = {
                'date': line.date,
                'journal_code': line.journal_id.code,
                'partner_id': line.partner_id.name,
                'ref': line.ref,
                'account_id': line.account_id.display_name,
                'move': line.move_name,
                'invoice_date': line.invoice_date,
                'entry_label': line.name,
                'debit': f"{line.debit:.2f} {line.company_currency_id.name}",
                'credit': f"{line.credit:.2f} {line.company_currency_id.name}"
            }
            vals.append(line_vals)

        currency_id = self.company_id.currency_id.name
        currency_debit_total = f"{total_debit:.2f} {currency_id}"
        currency_credit_total = f"{total_credit:.2f} {currency_id}"

        if not vals:
            raise ValidationError(_('No data in this date range'))

        data = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'company_name': self.company_id.name,
            'company_zip': self.company_id.zip,
            'company_phone': self.company_id.phone,
            'company_mobile': self.company_id.mobile,
            'company_email': self.company_id.email,
            'company_website': self.company_id.website,
            'company_state': self.company_id.state_id.name,
            'company_country': self.company_id.country_id.code,
            'journal_code': journal_code,
            'values': vals,
            'company_currency': self.company_id.currency_id.name,
            'debit_total': currency_debit_total,
            'credit_total': currency_credit_total,
        }

        return self.env.ref('kg_mashirah_oil_accounting.kg_day_book_report_action').with_context(
            landscape=False).report_action(self, data=data)

    def print_day_book_xlsx(self):
        if self.start_date > self.end_date:
            raise ValidationError(_('Start Date must be less than End Date'))

        active_ids_tmp = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')
        data = {

            'form': self.read()[0],
            'ids': active_ids_tmp,
            'context': {'active_modestock.movel': active_model},
        }

        file_io = BytesIO()
        workbook = xlsxwriter.Workbook(file_io)

        self.generate_xlsx_report(workbook, data=data)

        workbook.close()
        fout = encodebytes(file_io.getvalue())

        start_date = self.start_date.strftime("%d/%m/%Y")
        end_date = self.end_date.strftime("%d/%m/%Y")

        report_name = 'Day Book Report ' + str(start_date) + ' - ' + str(end_date)
        self.write({'fileout': fout, 'fileout_filename': report_name})
        file_io.close()

        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': 'web/content/?model=' + self._name + '&id=' + str(
                self.id) + '&field=fileout&download=true&filename=' + report_name,
        }

    def generate_xlsx_report(self, workbook, data=None, objs=None):
        # Create formats for the Excel sheet
        head = workbook.add_format({'align': 'left', 'bold': True, 'font_color': '#003366', 'font_size': '20px'})
        cell_format = workbook.add_format({'font_size': '12px'})
        cell_format_to = workbook.add_format({'font_size': '12px', 'align': 'left'})

        format1 = workbook.add_format({'font_size': 10, 'align': 'center', 'border': 1})
        format6 = workbook.add_format({'font_size': 10, 'align': 'center', 'border': 1, 'bold': True})
        format4 = workbook.add_format({'font_size': 10, 'align': 'left', 'border': 1})
        format5 = workbook.add_format({'font_size': 10, 'align': 'right', 'border': 1,'bold': True})
        format7 = workbook.add_format({'font_size': 10, 'align': 'right', 'border': 1, 'num_format': '0.000'})
        format2 = workbook.add_format({'font_size': 10, 'align': 'center', 'bold': True, 'border': 1})
        format3 = workbook.add_format({'font_size': 10, 'align': 'center', 'bold': True, 'border': 1})
        format_comment = workbook.add_format({'font_size': 10, 'align': 'left', 'border': 1, 'text_wrap': True})

        aml_ids = self.env['account.move.line'].search([
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date),
            ('parent_state', '=', 'posted'),
            ('company_id', '=', self.company_id.id)
        ], order='date asc')

        journal_ids = list(set(aml_ids.mapped('journal_id.code')))
        journal_code = ', '.join(journal_ids)

        # Create a new worksheet
        sheet = workbook.add_worksheet('Day Book Report')
        sheet.merge_range('A1:B2', 'Day Book Report', head)
        date_range_text_FROM = f"Journals: {journal_code} "
        sheet.merge_range('A4:B4', date_range_text_FROM, cell_format)
        date_range_text_TO = f" Target Moves: {'All Posted Entries'}"
        sheet.merge_range('D4:E4', date_range_text_TO, cell_format_to)
        date_range_text_FROM = f"Date From: {self.start_date.strftime('%d/%m/%Y')} "
        sheet.merge_range('A6:B6', date_range_text_FROM, cell_format)
        date_range_text_TO = f" Date To: {self.end_date.strftime('%d/%m/%Y')}"
        sheet.merge_range('D6:E6', date_range_text_TO, cell_format_to)

        # Headers and their column positions
        headers = ['Date', 'Journal Code', 'Partner Name', 'Reference', 'Account', 'Document Sequence', 'Invoice Date',
                   'Entry Label', 'Debit', 'Credit']
        col_start = 0  # Start column for data
        row_start = 8  # Start row for data

        # Set column widths
        column_widths = [15, 15, 20, 30, 15, 20, 15, 75, 12, 12]
        for col, width in enumerate(column_widths, start=col_start):
            sheet.set_column(col, col, width)

        # Write headers with specific formats
        for col, header in enumerate(headers, start=col_start):
            if header in ['Journal Code', 'Partner Name', 'Reference', 'Entry Label', 'Document Sequence']:
                sheet.write(row_start, col, header, format2)
            else:
                sheet.write(row_start, col, header, format6)

        # Fetch data
        row_number = row_start + 1

        if aml_ids:
            t_qty, t_price, t_subtotal, t_total = 0.000, 0.000, 0.000, 0.00

            for rec in aml_ids:
                sheet.write(row_number, col_start, rec.date.strftime('%d-%m-%Y'), format1)
                sheet.write(row_number, col_start + 1, rec.journal_id.code or '', format1)
                sheet.write(row_number, col_start + 2, rec.partner_id.name or '', format4)
                sheet.write(row_number, col_start + 3, rec.ref or '', format4)
                sheet.write(row_number, col_start + 4, rec.account_id.code or '', format1)
                sheet.write(row_number, col_start + 5, rec.move_id.name or '', format4)
                sheet.write(row_number, col_start + 6,
                            rec.invoice_date.strftime('%d-%m-%Y') if rec.invoice_date else '', format1)
                sheet.write(row_number, col_start + 7, rec.name or '', format4)
                sheet.write(row_number, col_start + 8, rec.debit, format7)
                sheet.write(row_number, col_start + 9, rec.credit, format7)

                # Accumulate totals
                t_qty += rec.debit
                t_price += rec.credit

                row_number += 1

            # Write totals
            sheet.write(row_number, col_start + 7, 'Total', format3)
            sheet.write(row_number, col_start + 8, t_qty, format5)
            sheet.write(row_number, col_start + 9, t_price, format5)

        # Define the table range
        table_range = f'A{row_start + 1}:J{row_number}'

        # Add a table to the worksheet
        sheet.add_table(table_range, {
            'columns': [{'header': header} for header in headers],
            'name': 'DayBookTable',
            'style': 'Table Style Medium 9',
            'banded_rows': True,
            'auto_filter': True
        })
