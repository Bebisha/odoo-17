from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
import xlsxwriter
from io import BytesIO

try:
	from base64 import encodebytes
except ImportError:
	from base64 import encodestring as encodebytes

class PaidInvoiceDetails(models.TransientModel):
    """Paid Invoice Details wizard."""

    _name = 'paid.invoice.detail.wizard'
    _description = 'Report Wizard'

    date_from = fields.Date('From Date')
    date_to = fields.Date('To Date')
    fileout = fields.Binary('File', readonly=True)
    fileout_filename = fields.Char('Filename', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)


    def print_xlsx(self):
        # active_ids_tmp = self.env.context.get('active_ids')
        # active_model = self.env.context.get('active_model')
        # data = {
        #     # 'output_type': self.read()[0]['output_type'][0],
        #     'ids': active_ids_tmp,
        #     'context': {'active_model': active_model},
        # }
        file_io = BytesIO()
        workbook = xlsxwriter.Workbook(file_io)

        self.generate_xlsx_report(workbook)

        workbook.close()
        fout = encodebytes(file_io.getvalue())
        datetime_string = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_name = 'Paid Invoice Report'
        filename = '%s_%s' % (report_name, datetime_string)
        self.write({'fileout': fout, 'fileout_filename': filename})
        file_io.close()
        filename += '%2Exlsx'

        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': 'web/content/?model=' + self._name + '&id=' + str(
                self.id) + '&field=fileout&download=true&filename=' + filename,
        }

    def generate_xlsx_report(self, workbook, data=None, objs=None):
        bold = workbook.add_format({'bold': True})
        cs_grp_gs = workbook.add_format({'border': 1, 'color': 'red', 'align': 'center'})
        text_bold = workbook.add_format({'border': 1, 'bg_color': '#ddd4f3', 'align': 'left', 'bold': True})
        reorder_sheet = workbook.add_worksheet("PAID INVOICE REPORT")
        row = 0
        # reorder_sheet.write()
        reorder_sheet.write(row, 0, self.company_id.name, bold)
        row += 1
        reorder_sheet.write(row, 0, 'Paid Invoice Between:'+str(self.date_from.strftime('%d-%m-%Y'))+str(self.date_to.strftime('%d-%m-%Y')), bold)
        row += 1
        reorder_sheet.write(row, 4, 'PAID CUSTOMER INVOICE REPORT', cs_grp_gs)
        row += 1
        reorder_sheet.write(row, 0, 'Sr #', text_bold)
        reorder_sheet.write(row, 1, 'Payment Reference ', text_bold)
        reorder_sheet.write(row, 2, 'Invoice Reference', text_bold)
        reorder_sheet.write(row, 3, 'VAT Amount', text_bold)
        reorder_sheet.write(row, 4, 'Invoice Amount', text_bold)
        reorder_sheet.write(row, 5, 'Invoice Due Date', text_bold)
        reorder_sheet.write(row, 6, 'Paid Amount', text_bold)
        reorder_sheet.write(row, 7, 'Paid Date', text_bold)
        cust_payments = self.env['account.payment'].search([('payment_type', '=', 'inbound'),
                                                            ('date', '>=', self.date_from), ('company_id', '=', self.env.company.id),
                                                            ('date', '<=', self.date_to)])
        index = 1
        for cust_pay in cust_payments:
            for cust_inv in cust_pay.reconciled_invoice_ids:
                row += 1
                reorder_sheet.write(row, 0, index, bold)
                reorder_sheet.write(row, 1, cust_pay.name, bold)
                reorder_sheet.write(row, 2, cust_inv.name, bold)
                reorder_sheet.write(row, 3, cust_inv.amount_tax_signed, bold)
                reorder_sheet.write(row, 4, cust_inv.amount_total_signed, bold)
                reorder_sheet.write(row, 5, cust_inv.invoice_date_due.strftime('%d-%m-%Y'), bold)
                reorder_sheet.write(row, 6, cust_pay.amount_company_currency_signed, bold)
                reorder_sheet.write(row, 7, cust_pay.date.strftime('%d-%m-%Y'), bold)
                index += 1

        row += 3
        reorder_sheet.write(row, 4, 'PAID VENDOR BILL REPORT', cs_grp_gs)
        row += 1
        reorder_sheet.write(row, 0, 'Sr #', text_bold)
        reorder_sheet.write(row, 1, 'Payment Reference ', text_bold)
        reorder_sheet.write(row, 2, 'Invoice Reference', text_bold)
        reorder_sheet.write(row, 3, 'VAT Amount', text_bold)
        reorder_sheet.write(row, 4, 'Invoice Amount', text_bold)
        reorder_sheet.write(row, 5, 'Invoice Due Date', text_bold)
        reorder_sheet.write(row, 6, 'Paid Amount', text_bold)
        reorder_sheet.write(row, 7, 'Paid Date', text_bold)
        vend_payments = self.env['account.payment'].search([('payment_type', '=', 'outbound'),
                                                            ('date', '>=', self.date_from),
                                                            ('company_id', '=', self.env.company.id),
                                                            ('date', '<=', self.date_to)])
        index = 1
        for vend_pay in vend_payments:
            for vend_inv in vend_pay.reconciled_bill_ids:
                row += 1
                reorder_sheet.write(row, 0, index, bold)
                reorder_sheet.write(row, 1, vend_pay.name, bold)
                reorder_sheet.write(row, 2, vend_inv.name, bold)
                reorder_sheet.write(row, 3, abs(vend_inv.amount_tax_signed), bold)
                reorder_sheet.write(row, 4, abs(vend_inv.amount_total_signed), bold)
                reorder_sheet.write(row, 5, vend_inv.invoice_date_due.strftime('%d-%m-%Y'), bold)
                reorder_sheet.write(row, 6, abs(vend_pay.amount_company_currency_signed), bold)
                reorder_sheet.write(row, 7, vend_pay.date.strftime('%d-%m-%Y'), bold)

                index += 1







