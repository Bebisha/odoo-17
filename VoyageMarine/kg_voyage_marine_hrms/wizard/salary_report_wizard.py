from base64 import encodebytes
from datetime import date
from io import BytesIO
import datetime

import pytz

from odoo import models, fields, _, api
from odoo.exceptions import ValidationError, UserError
from functools import reduce

import logging
import calendar
_logger = logging.getLogger(__name__)

try:
    from odoo.tools.misc import xlsxwriter, DEFAULT_SERVER_DATETIME_FORMAT
except ImportError:
    import xlsxwriter


class SalaryReportWizardReportWizard(models.TransientModel):
    _name = "salary.report.wizard"
    _description = "Salary Report Wizard"

    name = fields.Char(string="Name")
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  default=lambda self: self.env.company.currency_id.id)
    company_id = fields.Many2one(comodel_name='res.company', default=lambda self: self.env.user.company_id,
                                 string='Company')
    date_from = fields.Date()
    date_to = fields.Date()
    fileout = fields.Binary('File', readonly=True)
    fileout_filename = fields.Char('Filename', readonly=True)

    @api.onchange('date_from')
    def _onchange_date_from(self):
        if self.date_from:
            year = self.date_from.year
            month = self.date_from.month
            last_day = calendar.monthrange(year, month)[1]
            self.date_to = date(year, month, last_day)

    print_month = fields.Selection(
        [(str(num), month) for num, month in enumerate(
            ['JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE', 'JULY', 'AUGUST', 'SEPTEMBER', 'OCTOBER',
             'NOVEMBER', 'DECEMBER'], 1)],
        string="Month"
    )

    print_year = fields.Char(string="Year")

    @api.onchange('date_from')
    def get_month_year(self):
        if self.date_from:
            self.print_month = str(self.date_from.month)
            self.print_year = self.date_from.year
        else:
            self.print_month = False
            self.print_year = False

    def print_salary_xlsx(self):
        if self.date_from > self.date_to:
            raise ValidationError(_('Start Date must be less than End Date'))

        if self.date_from and self.date_to:
            if self.date_from.month != self.date_to.month:
                raise UserError(_('The Payslip of the same month will be printed'))

        payslip_ids = self.env['hr.payslip'].search(
            [('date_from', '>=', self.date_from), ('date_to', '<=', self.date_to)])

        if not payslip_ids:
            raise ValidationError(_('No data in this date range'))

        active_ids_tmp = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')
        data = {

            'form': self.read()[0],
            'ids': active_ids_tmp,
            'context': {'active_modelsalary.reportl': active_model},
        }

        file_io = BytesIO()
        workbook = xlsxwriter.Workbook(file_io)

        self.generate_xlsx_report(workbook, data=data)

        workbook.close()
        fout = encodebytes(file_io.getvalue())

        report_name = 'Salary Report'
        self.write({'fileout': fout, 'fileout_filename': report_name})
        file_io.close()

        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': 'web/content/?model=' + self._name + '&id=' + str(
                self.id) + '&field=fileout&download=true&filename=' + report_name,
        }

    def generate_xlsx_report(self, workbook, data=None, objs=None):
        sheet = workbook.add_worksheet('Salary Report')

        sheet.set_column(0, 0, 5)
        sheet.set_column(1, 1, 20)
        sheet.set_column(2, 2, 35)
        sheet.set_column(3, 3, 30)
        sheet.set_column(4, 4, 20)
        sheet.set_column(5, 5, 20)
        sheet.set_column(6, 6, 25)
        sheet.set_column(7, 7, 20)
        sheet.set_column(8, 8, 15)
        sheet.set_column(9, 9, 15)
        sheet.set_column(10, 10, 15)
        sheet.set_column(11, 11, 15)
        sheet.set_column(12, 12, 20)
        sheet.set_column(13, 13, 20)
        sheet.set_column(14, 14, 25)
        sheet.set_column(15, 15, 20)
        sheet.set_column(16, 16, 20)
        sheet.set_column(17, 17, 15)
        sheet.set_column(18, 18, 15)
        sheet.set_column(19, 19, 15)
        sheet.set_column(20, 20, 15)
        sheet.set_column(21, 21, 15)
        sheet.set_column(22, 22, 15)
        sheet.set_column(23, 23, 15)
        sheet.set_column(24, 24, 15)
        sheet.set_column(25, 25, 30)
        sheet.set_column(26, 26, 25)
        sheet.set_column(27, 27, 15)
        sheet.set_column(28, 28, 20)
        sheet.set_column(29, 29, 15)
        sheet.set_column(30, 30, 15)
        sheet.set_column(31, 31, 15)
        sheet.set_column(32, 32, 25)
        sheet.set_column(33, 33, 25)
        sheet.set_column(34, 34, 25)
        sheet.set_column(35, 35, 25)
        sheet.set_column(36, 36, 25)
        sheet.set_column(37, 37, 25)

        left_no_color = workbook.add_format({'bold': True, 'align': 'left', 'border': 1})
        center_no_cl_br = workbook.add_format({'align': 'center', 'border': 1})
        left_no_cl_br = workbook.add_format({'align': 'left', 'border': 1})
        right_no_cl_br = workbook.add_format({'align': 'right', 'border': 1})
        center_green = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#33cc33', 'border': 1})
        center_peacock_blue = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#9999ff', 'border': 1})
        center_blue = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#33ccff', 'border': 1})
        center_brown = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#e67300', 'border': 1})
        center_pink = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#ff99cc', 'border': 1})
        center_dark_blue = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#0099e6', 'border': 1})
        center_yellow = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#ffff66', 'border': 1})
        center_red = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#ffb399', 'border': 1})

        right_no_cl_br_decimal = workbook.add_format({'align': 'right', 'border': 1, 'num_format': '#,##0.00'})

        row = 0
        col = 0
        formatted_date = self.date_from.strftime('%B %Y').upper()

        sheet.merge_range(row, col, row, col + 5, f'VOYAGE MARINE GROUP - SALARY  - {formatted_date}', left_no_color)

        row = row + 1
        col = col
        sheet.merge_range(row, col, row, col + 5, '')

        row = row + 1
        col = col
        sheet.merge_range(row, col, row, col + 5, 'VOYAGE MARINE AUTOMATION LLC  VISA -WPS', left_no_color)

        row = row + 1
        col = col
        sheet.merge_range(row, col, row, col + 5, '')

        row = row + 1
        col = col
        sheet.merge_range(row, col, row, col + 3, 'EMPLOYEES DETAILS', center_green)
        sheet.merge_range(row, col + 4, row, col + 7, 'CALCULATION', center_peacock_blue)
        sheet.merge_range(row, col + 8, row, col + 17, 'FIXED INCOME', center_green)
        sheet.merge_range(row, col + 18, row, col + 28, 'VARIABLE INCOME-MONTHLY ENTRY', center_peacock_blue)
        sheet.merge_range(row, col + 30, row, col + 35, 'DEDUCTIONS', center_green)

        row = row + 1
        col = col
        sheet.write(row, col, 'Sl.No', center_blue)
        sheet.write(row, col + 1, 'Empl.Code', center_blue)
        sheet.write(row, col + 2, 'Name', center_blue)
        sheet.write(row, col + 3, 'Department', center_blue)
        sheet.write(row, col + 4, 'No. of Working days', center_brown)
        sheet.write(row, col + 5, 'No. of Leaves Taken', center_brown)
        sheet.write(row, col + 6, 'Deduction / Unpaid Leaves', center_brown)
        sheet.write(row, col + 7, 'Total Paid Days', center_brown)
        sheet.write(row, col + 8, 'Basic Pay', center_pink)
        sheet.write(row, col + 9, 'HRA', center_pink)
        sheet.write(row, col + 10, 'Food Allowance', center_pink)
        sheet.write(row, col + 11, 'DA', center_pink)
        sheet.write(row, col + 12, 'Telephone Allowance', center_pink)
        sheet.write(row, col + 13, 'Special Allowance', center_pink)
        sheet.write(row, col + 14, 'Performance Allowance', center_pink)
        sheet.write(row, col + 15, 'Transport Allowance', center_pink)
        sheet.write(row, col + 16, 'Fixed OT Allowance', center_pink)
        sheet.write(row, col + 17, 'Fixed Total', center_pink)
        sheet.write(row, col + 18, 'OT  Rate', center_dark_blue)
        sheet.write(row, col + 19, 'No.of OT Hrs.', center_dark_blue)
        sheet.write(row, col + 20, 'Total OT', center_dark_blue)
        sheet.write(row, col + 21, 'Overseas', center_dark_blue)
        sheet.write(row, col + 22, 'Anchorage', center_dark_blue)
        sheet.write(row, col + 23, 'Ticket', center_dark_blue)
        sheet.write(row, col + 24, 'Leave Salary', center_dark_blue)
        sheet.write(row, col + 25, 'Performance Allowance-Monthly', center_dark_blue)
        sheet.write(row, col + 26, 'Sales/Service Incentives', center_dark_blue)
        sheet.write(row, col + 27, 'OT LUMPSUM', center_dark_blue)
        sheet.write(row, col + 28, 'Variable Total', center_dark_blue)
        sheet.write(row, col + 29, 'Gross Total', center_yellow)
        sheet.write(row, col + 30, 'CASH ADVANCE', center_red)
        sheet.write(row, col + 31, 'HRA', center_red)
        sheet.write(row, col + 32, 'Telephone Deduction', center_red)
        sheet.write(row, col + 33, 'Vehicle Fine', center_red)
        sheet.write(row, col + 34, 'OTHER', center_red)
        sheet.write(row, col + 35, 'Total Deductions', center_red)
        sheet.write(row, col + 36, 'NET PAY', center_yellow)
        sheet.write(row, col + 37, 'Remarks', left_no_color)

        row = row + 1
        col = col

        payslip_ids = self.env['hr.payslip'].search(
            [('date_from', '>=', self.date_from), ('date_to', '<=', self.date_to)])

        if payslip_ids:
            i = 1
            for pay in payslip_ids:
                sheet.write(row, col, i, center_no_cl_br)

                sheet.write(row, col + 1,
                            pay.employee_id.registration_number if pay.employee_id.registration_number else '',
                            center_no_cl_br)

                sheet.write(row, col + 2, pay.employee_id.name if pay.employee_id.name else '', left_no_cl_br)

                sheet.write(row, col + 3, pay.employee_id.department_id.name if pay.employee_id.department_id else '',
                            left_no_cl_br)
                if pay.date_from:
                    year = pay.date_from.year
                    month = pay.date_from.month
                    total_days = calendar.monthrange(year, month)[1]
                else:
                    total_days = 0

                # sheet.write(row, col + 4, pay.working_days if pay.working_days else '', center_no_cl_br)
                sheet.write(row, col + 4, total_days if total_days else '', center_no_cl_br)

                sheet.write(row, col + 5, pay.total_leave_days if pay.total_leave_days else '', center_no_cl_br)

                sheet.write(row, col + 6, pay.total_unpaid_leaves if pay.total_unpaid_leaves else '',
                            center_no_cl_br)

                # paid_days = pay.working_days - pay.total_unpaid_leaves
                if pay.date_from:
                    year = pay.date_from.year
                    month = pay.date_from.month
                    total_days = calendar.monthrange(year, month)[1]
                else:
                    total_days = 0
                # sheet.write(row, col + 7, paid_days if paid_days else '', center_no_cl_br)
                sheet.write(row, col + 7, total_days if total_days else '', center_no_cl_br)

                sheet.write(row, col + 8, pay.paid_amount if pay.contract_id and pay.paid_amount else '',
                            right_no_cl_br_decimal)

                sheet.write(row, col + 9,
                            pay.contract_id.l10n_ae_housing_allowance if pay.contract_id and pay.contract_id.l10n_ae_housing_allowance else '',
                            right_no_cl_br_decimal)

                sheet.write(row, col + 10,
                            pay.contract_id.food_allowance if pay.contract_id and pay.contract_id.food_allowance else '',
                            right_no_cl_br_decimal)

                sheet.write(row, col + 11,
                            pay.contract_id.da_allowance if pay.contract_id and pay.contract_id.da_allowance else '',
                            right_no_cl_br_decimal)

                sheet.write(row, col + 12,
                            pay.contract_id.telephone_allowance if pay.contract_id and pay.contract_id.telephone_allowance else '',
                            right_no_cl_br_decimal)

                sheet.write(row, col + 13,
                            pay.contract_id.special_allowance if pay.contract_id and pay.contract_id.special_allowance else '',
                            right_no_cl_br_decimal)

                sheet.write(row, col + 14,
                            pay.contract_id.performance_allowance if pay.contract_id and pay.contract_id.performance_allowance else '',
                            right_no_cl_br_decimal)

                sheet.write(row, col + 15,
                            pay.contract_id.l10n_ae_transportation_allowance if pay.contract_id and pay.contract_id.l10n_ae_transportation_allowance else '',
                            right_no_cl_br_decimal)

                sheet.write(row, col + 16,
                            pay.fixed_ot_allowance if pay.fixed_ot_allowance else '',
                            right_no_cl_br_decimal)


                fixed_total = pay.paid_amount + pay.contract_id.l10n_ae_housing_allowance + pay.contract_id.food_allowance + pay.contract_id.da_allowance + pay.contract_id.telephone_allowance + pay.contract_id.special_allowance + pay.contract_id.performance_allowance + pay.contract_id.l10n_ae_transportation_allowance + pay.fixed_ot_allowance
                sheet.write(row, col + 17, fixed_total if fixed_total else '', right_no_cl_br_decimal)

                if pay.contract_id.ot_wage == 'hourly_fixed':
                    ot_rate = pay.contract_id.hourly_ot_allowance
                elif pay.contract_id.ot_wage == 'daily_fixed':
                    ot_rate = pay.contract_id.over_time
                else:
                    ot_rate = 0.00

                sheet.write(row, col + 18, ot_rate if ot_rate else '', right_no_cl_br_decimal)

                employee_entry_ids = self.env['hr.employee.entry'].search(
                    [('employee_id', '=', pay.employee_id.id), ('start_date', '>=', self.date_from),
                     ('end_date', '<=', self.date_to), ('type_entry', 'in', ['overtime', 'overtime_fixed_allowance'])])
                ot_hours = sum(employee_entry_ids.mapped('duration')) if employee_entry_ids else 0.00
                total_ot = sum(employee_entry_ids.mapped('over_time')) if employee_entry_ids else 0.00

                sheet.write(row, col + 19, ot_hours if ot_hours else '', center_no_cl_br)
                sheet.write(row, col + 20, total_ot if total_ot else '', right_no_cl_br_decimal)
                anchorage_amount = 0.0
                if pay.input_line_ids:
                    anchorage_input = pay.input_line_ids.filtered(
                        lambda x: x.input_type_id.id == self.env.ref(
                            'kg_voyage_marine_hrms.anchorage_input_type'
                        ).id
                    )

                    if anchorage_input:
                        anchorage_amount = sum(anchorage_input.mapped('amount'))

                overseas_amount = 0.0
                if pay.input_line_ids:
                    overseas_input = pay.input_line_ids.filtered(
                        lambda x: x.input_type_id.id == self.env.ref(
                            'kg_voyage_marine_hrms.overseas_input_type'
                        ).id
                    )
                    if overseas_input:
                        overseas_amount = sum(overseas_input.mapped('amount'))

                sheet.write(row, col + 21, overseas_amount if overseas_amount else '', right_no_cl_br_decimal)

                sheet.write(
                    row,
                    col + 22,
                    anchorage_amount if anchorage_amount != 0.0 else '',
                    right_no_cl_br_decimal
                )

                ticket_amount = 0.00
                if pay.input_line_ids:
                    print(pay.input_line_ids,"pay.input_line_ids")
                    for line in pay.input_line_ids:
                        print(line.input_type_id.name, "input line name")
                    ticket = pay.input_line_ids.filtered(
                        lambda x: x.input_type_id.id == self.env.ref('kg_voyage_marine_hrms.ticket_input_type').id)
                    if ticket:
                        ticket_amount = sum(ticket.mapped('amount'))
                sheet.write(row, col + 23, ticket_amount if ticket_amount != 0.00 else '', right_no_cl_br_decimal)

                leave_salary_amount = 0.00
                if pay.input_line_ids:
                    leave_salary = pay.input_line_ids.filtered(
                        lambda x: x.input_type_id.id == self.env.ref(
                            'kg_voyage_marine_hrms.leave_salary_input_type').id)
                    if leave_salary:
                        leave_salary_amount = sum(leave_salary.mapped('amount'))
                sheet.write(row, col + 24, leave_salary_amount if leave_salary_amount != 0.00 else '',
                            right_no_cl_br_decimal)

                perf_alw_monthly_amount = 0.00
                if pay.input_line_ids:
                    perf_alw_monthly = pay.input_line_ids.filtered(
                        lambda x: x.input_type_id.id == self.env.ref(
                            'kg_voyage_marine_hrms.performance_allowance_monthly_input_type').id)
                    if perf_alw_monthly:
                        perf_alw_monthly_amount = sum(perf_alw_monthly.mapped('amount'))
                sheet.write(row, col + 25, perf_alw_monthly_amount if perf_alw_monthly_amount != 0.00 else '',
                            right_no_cl_br_decimal)

                sale_service_incentive_amount = 0.00
                if pay.input_line_ids:
                    sale_service_incentive = pay.input_line_ids.filtered(
                        lambda x: x.input_type_id.id == self.env.ref(
                            'kg_voyage_marine_hrms.sales_service_incentives_input_type').id)
                    if sale_service_incentive:
                        sale_service_incentive_amount = sum(sale_service_incentive.mapped('amount'))
                sheet.write(row, col + 26,
                            sale_service_incentive_amount if sale_service_incentive_amount != 0.00 else '',
                            right_no_cl_br_decimal)

                ot_lumpsum_amount = 0.00
                if pay.input_line_ids:
                    ot_lumpsum = pay.input_line_ids.filtered(
                        lambda x: x.input_type_id.id == self.env.ref('kg_voyage_marine_hrms.ot_lumpsum_input_type').id)
                    if ot_lumpsum:
                        ot_lumpsum_amount = sum(ot_lumpsum.mapped('amount'))
                sheet.write(row, col + 27, ot_lumpsum_amount if ot_lumpsum_amount != 0.00 else '',
                            right_no_cl_br_decimal)

                variable_total = total_ot + overseas_amount + anchorage_amount + ticket_amount + leave_salary_amount + perf_alw_monthly_amount + sale_service_incentive_amount + ot_lumpsum_amount
                sheet.write(row, col + 28, variable_total if variable_total else '', right_no_cl_br_decimal)

                gross_total = fixed_total + variable_total
                sheet.write(row, col + 29, gross_total if gross_total else '', right_no_cl_br_decimal)

                cash_advance_amount = 0.00
                if pay.input_line_ids:
                    cash_advance = pay.input_line_ids.filtered(
                        lambda x: x.input_type_id.id == self.env.ref(
                            'kg_voyage_marine_hrms.cash_advance_input_type').id)
                    if cash_advance:
                        cash_advance_amount = sum(cash_advance.mapped('amount'))
                sheet.write(row, col + 30, cash_advance_amount if cash_advance_amount != 0.00 else '',
                            right_no_cl_br_decimal)

                sheet.write(row, col + 31,
                            pay.contract_id.hra_deduction if pay.contract_id and pay.contract_id.hra_deduction else '',
                            right_no_cl_br_decimal)

                sheet.write(row, col + 32,
                            pay.contract_id.telephone_deduction if pay.contract_id and pay.contract_id.telephone_deduction else '',
                            right_no_cl_br_decimal)

                vehicle_fine_amount = 0.00
                if pay.input_line_ids:
                    vehicle_fine = pay.input_line_ids.filtered(
                        lambda x: x.input_type_id.id == self.env.ref(
                            'kg_voyage_marine_hrms.vehicle_fine_input_type').id)
                    if vehicle_fine:
                        vehicle_fine_amount = sum(vehicle_fine.mapped('amount'))
                sheet.write(row, col + 33, vehicle_fine_amount if vehicle_fine_amount != 0.00 else '',
                            right_no_cl_br_decimal)

                sheet.write(row, col + 34, '', right_no_cl_br_decimal)

                total_deductions = pay.contract_id.hra_deduction + pay.contract_id.telephone_deduction + cash_advance_amount + vehicle_fine_amount
                sheet.write(row, col + 35, total_deductions if total_deductions else '', right_no_cl_br_decimal)

                total_net_pay = gross_total - total_deductions
                sheet.write(row, col + 36, total_net_pay if total_net_pay else '', right_no_cl_br_decimal)

                sheet.write(row, col + 37, '', right_no_cl_br_decimal)

                i += 1
                row = row + 1
                col = col
