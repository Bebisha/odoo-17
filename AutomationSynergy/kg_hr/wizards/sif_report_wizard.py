from collections import OrderedDict

from odoo import fields, models, api, _
from base64 import encodebytes
from datetime import datetime, timedelta
from io import BytesIO
from odoo.exceptions import ValidationError, UserError

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class PayslipReportWizard(models.TransientModel):
    _name = "payslip.sif.report.wizard"
    _description = "Payroll report"

    date_from = fields.Date()
    date_to = fields.Date()
    # actual_deduction = fields.Boolean('Actual')
    # expact_wiz = fields.Boolean('Expact')
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, readonly=True,
                                 default=lambda self: self.env.company)
    fileout = fields.Binary('File', readonly=True)
    fileout_filename = fields.Char('Filename', readonly=True)
    @api.onchange('date_from','date_to')
    def onchange_date(self):
        if (self.date_from and self.date_to) and (self.date_from.month!=self.date_to.month):
            raise UserError('Please select dates within the same month.')

    def print_sif_xlsx(self):

        if self.date_from > self.date_to:
            raise ValidationError(_('Start Date must be less than End Date'))

        if self.date_from and self.date_to:
            if self.date_from.month != self.date_to.month:
                raise UserError(_('The Payslip of the same month will be printed'))

        """ button action to print xlsx report of Sif employees"""

        active_ids_tmp = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')
        data = {
            'form': self.read()[0],
            'ids': active_ids_tmp,
            'context': {'active_model': active_model},
        }
        file_io = BytesIO()
        workbook = xlsxwriter.Workbook(file_io)

        self.get_xlsx_report(workbook, data)
        workbook.close()
        fout = encodebytes(file_io.getvalue())
        datetime_string = datetime.now().strftime("%Y-%m-%d")
        report_name = 'SIF Report'
        if self.company_id.bank_ids:
            report_name = str(self.company_id.bank_ids[0].acc_number)

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

    def get_xlsx_report(self, workbook, data, ):

        from_date = self.date_from
        to_date = self.date_to

        cell_format = workbook.add_format(
            {'font_size': '12px', 'align': 'center'})

        header_row_style = workbook.add_format({'bold': True, 'align': 'center', 'border': True})

        sheet = workbook.add_worksheet()
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '13px'})

        txt = workbook.add_format({'font_size': '10px', 'align': 'left'})

        date_style = workbook.add_format(
            {'text_wrap': True, 'font_size': '10px', 'num_format': 'dd-mm-yyyy', 'align': 'left'})

        amt = workbook.add_format({'font_size': '10px', 'align': 'right'})
        sl_no = workbook.add_format({'font_size': '10px', 'align': 'center'})

        bold = workbook.add_format({'bold': True, 'font_size': '8px', 'align': 'center'})
        bold_total = workbook.add_format({'bold': True, 'font_size': '10px', 'align': 'center'})
        bold_total_amount = workbook.add_format({'bold': True, 'font_size': '10px', 'align': 'right'})

        row = 0
        col = 0
        payslip_obj = self.env['hr.payslip'].search(
            [('date_from', '>=', self.date_from), ('date_to', '<=', self.date_to), ('state', '=', 'done')])
        payslip_lines = payslip_obj.mapped('line_ids')
        allowances = payslip_lines.filtered(lambda l: l.category_id.code == 'ALW').mapped(
            'name')
        deductions = payslip_lines.filtered(lambda l: l.category_id.code == 'DED').mapped(
            'name')
        basic = payslip_lines.filtered(lambda l: l.category_id.code == 'BASIC').mapped(
            'name')

        sheet.merge_range(row, col, row + 1,
                          col + 11,
                          'SIF Report', head)
        sheet.merge_range(row + 2, col, row + 2, col + 2, 'Date Range:', bold)
        sheet.merge_range(row + 2, col + 3, row + 2, col + 5,
                          '%s - %s ' % (self.date_from.strftime('%d-%m-%Y'), self.date_to.strftime('%d-%m-%Y')),
                          date_style)
        sheet.set_column(row, col, 8)
        sheet.set_column(row + 1, col + 1, 20)
        sheet.set_column(row + 2, col + 2, 15)
        sheet.set_column(row + 3, col + 3, 20)
        sheet.set_row(row + 2, 30)
        sheet.set_row(row + 3, 30)
        sheet.write(row + 3, col, 'SL. No.', bold)
        sheet.write(row + 3, col + 1, 'Personal No.', bold)
        sheet.write(row + 3, col + 2, 'Employee Name', bold)

        sheet.write(row + 3, col + 3, 'Routing Code', bold)
        sheet.write(row + 3, col + 4, 'Account No.', bold)
        sheet.write(row + 3, col + 5, 'Fixed Salary', bold)
        sheet.write(row + 3, col + 6, 'Variable Salary', bold)
        sheet.write(row + 3, col + 7, 'Month', bold)
        sheet.write(row + 3, col + 8, 'Year', bold)
        sheet.write(row + 3, col + 9, 'Leave Days', bold)
        sheet.write(row + 3, col + 10, 'Remarks1', bold)
        sheet.write(row + 3, col + 11, 'Remarks1', bold)
        sheet.set_column(row + 4, col + 4, 25)
        sheet.set_column(row + 5, col + 5, 10)

        sheet.set_column(4, 4, 25)
        sheet.set_column(5, 5, 10)
        sheet.set_column(6, 6, 15)
        sheet.set_column(7, 7, 15)
        sheet.set_column(8, 8, 15)
        sheet.set_column(9, 9, 15)
        sheet.set_column(10, 10, 15)
        sheet.set_column(11, 11, 15)
        sheet.set_column(12, 12, 15)
        sheet.set_column(13, 13, 20)
        sheet.set_column(14, 14, 15)
        sheet.set_column(15, 15, 15)
        sheet.set_column(16, 16, 15)
        sheet.set_column(17, 17, 15)
        sheet.set_column(18, 18, 15)
        sheet.set_column(19, 19, 20)
        sheet.set_column(20, 20, 15)
        sheet.set_column(21, 21, 15)
        sheet.set_column(22, 22, 25)
        sheet.set_column(23, 23, 15)

        sheet.set_column(26, 26, 15)
        sheet.set_column(27, 27, 15)
        sheet.set_column(28, 28, 15)
        count = 1
        row = 4
        col = 0
        new_col = col

        total_amount = 0
        for paysl in payslip_obj:
            sheet.write(row, col, count, sl_no)
            sheet.write(row, col + 1, paysl.employee_id.personal_no or '', txt)
            sheet.write(row, col + 2, paysl.employee_id.name or '', txt)
            sheet.write(row, col + 3, paysl.employee_id.bank_account_id.bank_id.routing_code or '', txt)
            sheet.write(row, col + 4, paysl.employee_id.bank_account_id.acc_number or '', txt)
            basic_amount = sum(paysl.line_ids.filtered(lambda x: x.category_id.code == 'BASIC').mapped('total'))
            sheet.write(row, col + 5, basic_amount or '0', amt)

            # gross = basic_amount
            amnt = sum(paysl.line_ids.filtered(lambda x: x.category_id.code == 'ALW' and x.salary_rule_id.code != 'HRA').mapped('total'))
            ded = sum(paysl.line_ids.filtered(lambda x: x.category_id.code == 'DED').mapped('total'))
            net = amnt - ded
            sheet.write(row, col + 6, net or '0', amt)
            sheet.write(row, col + 7, self.date_from.strftime('%B'), txt)
            sheet.write(row, col + 8, self.date_from.strftime('%Y'), amt)

            row += 1
            col = 0
            count += 1
        workbook.close()
