from base64 import encodebytes
from datetime import date
from io import BytesIO
import datetime

import pytz

from odoo import models, fields, _
from odoo.exceptions import ValidationError, UserError
from functools import reduce

import logging

_logger = logging.getLogger(__name__)

try:
    from odoo.tools.misc import xlsxwriter, DEFAULT_SERVER_DATETIME_FORMAT
except ImportError:
    import xlsxwriter


class SIFReportWizard(models.TransientModel):
    _name = "sif.report.wizard"
    _description = "Salary Information File Report Wizard"

    name = fields.Char(string="Name")
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  default=lambda self: self.env.company.currency_id.id)
    company_id = fields.Many2one(comodel_name='res.company', default=lambda self: self.env.user.company_id,
                                 string='Company')
    date_from = fields.Date()
    date_to = fields.Date()
    fileout = fields.Binary('File', readonly=True)
    fileout_filename = fields.Char('Filename', readonly=True)

    def print_sif_xlsx(self):
        if self.date_from > self.date_to:
            raise ValidationError(_('Start Date must be less than End Date'))

        if self.date_from and self.date_to:
            if self.date_from.month != self.date_to.month:
                raise UserError(_('The Payslip of the same month will be printed'))

        if not self.company_id.company_code:
            raise UserError(_('Configure Your Company Code'))
        if not self.company_id.bank_ids:
            raise UserError(_('Configure Your Bank In Accounting Dashboard'))
        if not self.company_id.bank_ids[0].bank_id.routing_code:
            raise UserError(_('Configure Your Company Bank Routing Code'))
        if self.company_id.bank_ids and not self.company_id.bank_ids[0].bank_iban_number:
            raise UserError(_('Configure Your Company Bank IBAN Number'))

        payslip_id = self.env['hr.payslip'].search(
            [('date_from', '>=', self.date_from), ('date_to', '<=', self.date_to), ('state', 'in', ['paid', 'done']),
             ('company_id', '=', self.company_id.id)])
        payslip_employee_id = list(set(payslip_id.mapped('employee_id')))

        if not payslip_id:
            raise ValidationError(_('No data in this date range'))

        emp_reg = []
        emp_routing_code = []
        emp_iban_number = []

        for emp in payslip_employee_id:
            non_emp_reg = payslip_id.filtered(
                lambda x: x.employee_id.id == emp.id and x.employee_id.registration_number == False)

            non_routing_code = payslip_id.filtered(
                lambda x: x.employee_id.id == emp.id and x.employee_id.bank_account_id.bank_id.routing_code == False)

            non_iban_number = payslip_id.filtered(
                lambda x: x.employee_id.id == emp.id and x.employee_id.bank_account_id.bank_iban_number == False)

            if non_emp_reg:
                emp_reg.append(emp.name)
            if non_routing_code:
                emp_routing_code.append(emp.name)
            if non_iban_number:
                emp_iban_number.append(emp.name)

        get_emp_reg_name = ', '.join([str(elem) for elem in emp_reg])
        get_emp_routing_code = ', '.join([str(elem) for elem in emp_routing_code])
        get_emp_iban_number = ', '.join([str(elem) for elem in emp_reg])

        if emp_reg:
            raise UserError(_('Configure %s Employees Registration Number', get_emp_reg_name))

        if emp_routing_code:
            raise UserError(_('Configure  %s Employees Bank Routing Code', get_emp_routing_code))

        if emp_iban_number:
            raise UserError(_('Configure %s Employees Bank IBAN Number', get_emp_iban_number))

        active_ids_tmp = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')
        data = {

            'form': self.read()[0],
            'ids': active_ids_tmp,
            'context': {'active_modeaccount.movel': active_model},
        }

        file_io = BytesIO()
        workbook = xlsxwriter.Workbook(file_io)

        self.generate_xlsx_report(workbook, data=data)

        workbook.close()
        fout = encodebytes(file_io.getvalue())

        report_name = 'Salary Information File'
        self.write({'fileout': fout, 'fileout_filename': report_name})
        file_io.close()

        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': 'web/content/?model=' + self._name + '&id=' + str(
                self.id) + '&field=fileout&download=true&filename=' + report_name,
        }

    def generate_xlsx_report(self, workbook, data=None, objs=None):
        sheet = workbook.add_worksheet('Salary Information File')

        date_style = workbook.add_format({
            'text_wrap': True, 'num_format': 'yyyy-mm-dd', 'font_name': 'Calibri',
            'align': 'left', 'border': False
        })
        company_date_style = workbook.add_format({
            'text_wrap': True, 'num_format': 'mmyyyy', 'font_name': 'Calibri',
            'align': 'left', 'border': False
        })

        style_specification_data_white = workbook.add_format()
        style_specification_data_white.set_font_name('Calibri')
        style_specification_data_white.set_text_wrap()
        style_specification_data_white.set_align('left')

        sheet.set_column(0, 0, 5)
        sheet.set_column(1, 1, 25)
        sheet.set_column(2, 2, 25)
        sheet.set_column(3, 3, 25)
        sheet.set_column(4, 4, 10)
        sheet.set_column(5, 5, 10)
        sheet.set_column(6, 6, 5)
        sheet.set_column(7, 7, 15)
        sheet.set_column(8, 8, 15)
        sheet.set_column(9, 9, 25)

        row = 0
        col = 0

        payslip_id = self.env['hr.payslip'].search(
            [('date_from', '>=', self.date_from), ('date_to', '<=', self.date_to), ('state', 'in', ['paid', 'done']),
             ('company_id', '=', self.company_id.id)])

        count = 0
        total_salary = 0
        total_allowance = 0
        for pay in payslip_id:
            col = col

            sheet_number = 1

            employee_code = pay.employee_id.registration_number if pay.employee_id.registration_number else ''
            employee_routing_code = pay.employee_id.bank_account_id.bank_id.routing_code if pay.employee_id.bank_account_id.bank_id.routing_code else ''
            employee_bank_iban_number = pay.employee_id.bank_account_id.bank_iban_number if pay.employee_id.bank_account_id.bank_iban_number else ''
            start_date = pay.date_from if pay.date_from else ''
            end_date = pay.date_to if pay.date_to else ''
            number_of_days = reduce(lambda x, y: (y - x).days,
                                    [pay.date_from, pay.date_to]) if pay.date_from and pay.date_to else ''

            payslip_net_line_id = self.env['hr.payslip.line'].search(
                [('category_id', '=', self.env.ref('hr_payroll.NET').id), ('slip_id', '=', pay.id)])
            net_total_amount = sum(payslip_net_line_id.mapped('amount'))

            payslip_allowance_line_id = self.env['hr.payslip.line'].search(
                [('category_id', '=', self.env.ref('hr_payroll.ALW').id), ('slip_id', '=', pay.id)])
            allowance_total_amount = sum(payslip_allowance_line_id.mapped('amount'))

            salary = net_total_amount - allowance_total_amount if net_total_amount or allowance_total_amount else 0.00
            other_allowance = allowance_total_amount if allowance_total_amount else 0.00

            sheet.write(row, col, 'EDR', style_specification_data_white)
            sheet.write(row, col + 1, employee_code, style_specification_data_white)
            sheet.write(row, col + 2, employee_routing_code, style_specification_data_white)
            sheet.write(row, col + 3, employee_bank_iban_number, style_specification_data_white)
            sheet.write(row, col + 4, start_date, date_style)
            sheet.write(row, col + 5, end_date, date_style)
            sheet.write(row, col + 6, number_of_days + 1, style_specification_data_white)
            sheet.write(row, col + 7, f"{salary:.2f}", style_specification_data_white)
            sheet.write(row, col + 8, f"{other_allowance:.2f}", style_specification_data_white)
            sheet.write(row, col + 9, self.get_days(pay), style_specification_data_white)

            count += sheet_number
            total_salary += salary
            total_allowance += other_allowance
            row += 1
        company_code = self.company_id.company_code if self.company_id.company_code else ''

        company_routing_code = self.company_id.partner_id.bank_ids[0].bank_id.routing_code if \
            self.company_id.partner_id.bank_ids[0].bank_id.routing_code else ''

        company_bank_iban_number = self.company_id.partner_id.bank_ids[0].bank_iban_number if \
            self.company_id.partner_id.bank_ids[0].bank_iban_number else ''

        total = total_allowance + total_salary if total_salary or total_allowance else 0.00

        user_tz = self.env.user.tz or pytz.utc
        tz = pytz.timezone(user_tz)
        local_timezone = pytz.timezone(self.env.user.tz)
        current_hour = datetime.datetime.now().astimezone(local_timezone).hour
        current_min = datetime.datetime.now().astimezone(local_timezone).minute
        current_time = str(current_hour) + str(current_min)

        sheet.write(row, col, 'SCR', style_specification_data_white)
        sheet.write(row, col + 1, company_code, style_specification_data_white)
        sheet.write(row, col + 2, company_routing_code, style_specification_data_white)
        sheet.write(row, col + 3, date.today(), date_style)
        sheet.write(row, col + 4, current_time, style_specification_data_white)
        sheet.write(row, col + 5, date.today(), company_date_style)
        sheet.write(row, col + 6, count, style_specification_data_white)
        sheet.write(row, col + 7, f"{total:.2f}", style_specification_data_white)
        sheet.write(row, col + 8, '', style_specification_data_white)
        sheet.write(row, col + 9, company_bank_iban_number, style_specification_data_white)

    def get_days(self, slip_id):
        days = self.env['hr.payslip.worked_days'].search([('payslip_id', '=', slip_id.id)])
        total_days = sum(rec.number_of_days for rec in days)
        return total_days if total_days else 0
