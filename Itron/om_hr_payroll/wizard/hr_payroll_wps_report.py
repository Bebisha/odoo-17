import io
import base64
import xlsxwriter
from odoo import models, fields, api
from datetime import datetime, date
import calendar


class HrPayslipWpsWizard(models.TransientModel):
    _name = 'hr.payslip.wps.wizard'
    _description = 'WPS Wizard for HR Payslip'

    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.company)
    month_selection = fields.Selection(
        [
            ('01', 'January'),
            ('02', 'February'),
            ('03', 'March'),
            ('04', 'April'),
            ('05', 'May'),
            ('06', 'June'),
            ('07', 'July'),
            ('08', 'August'),
            ('09', 'September'),
            ('10', 'October'),
            ('11', 'November'),
            ('12', 'December')
        ], string="Month", required=True, default=lambda self: str(datetime.today().month).zfill(2)
    )
    year = fields.Char(string="Year", required=True, default=lambda self: str(datetime.today().year), readonly=True)

    def generate_wps_report(self):
        selected_month = self.month_selection
        selected_year = self.year

        first_day = f'{selected_year}-{selected_month}-01'
        last_day = f'{selected_year}-{selected_month}-{calendar.monthrange(int(selected_year), int(selected_month))[1]}'

        payslip_ids = self.env['hr.payslip'].search([
            ('date_from', '>=', first_day),
            ('date_to', '<=', last_day),
            ('company_id', '=', self.company_id.id),
            ('state', '=', 'done'),
        ])

        country_code = self.company_id.country_code

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Payslip Report')

        if country_code == 'BH':
            header_format = workbook.add_format(
                {'bold': True, 'bg_color': '#0D1F87', 'color': 'white', 'font_size': 10, 'align': 'center',
                 'valign': 'vcenter'})
            cell_format = workbook.add_format({'font_size': 10, 'border': 1, 'align': 'center', 'valign': 'vcenter'})
            number_format = workbook.add_format(
                {'num_format': '#,##0.00', 'border': 1, 'align': 'center', 'valign': 'vcenter'})


            worksheet.set_column('A:A', 25)
            worksheet.set_column('B:B', 25)
            worksheet.set_column('C:C', 25)
            worksheet.set_column('D:D', 25)
            worksheet.set_column('E:E', 25)

            worksheet.merge_range('B1:F1', 'Payslip Report', header_format)

            headers = ['Beneficiary Name', 'IBAN', 'Amount', 'Beneficiary CPR', 'Comments (Optional)']
            worksheet.write_row(3, 1, headers, header_format)

            row = 4
            for payslip in payslip_ids:
                employee_name = payslip.employee_id.name
                iban = payslip.employee_id.bank_account_id.acc_number
                basic_salary = sum(payslip.line_ids.filtered(lambda x: x.category_id.code == 'BASIC').mapped('total'))
                cpr = payslip.employee_id.bank_account_id.beneficiary_cpr 

                worksheet.write_row(row, 1, [employee_name, iban, basic_salary, cpr, ''], cell_format)
                row += 1

            worksheet.set_column('B:F', 25, number_format)

        elif country_code == 'OM':

            header_format = workbook.add_format(
                {'bold': True, 'color': 'black', 'font_size': 10, 'align': 'center',
                 'valign': 'vcenter'})
            cell_format = workbook.add_format({'font_size': 10, 'border': 1, 'align': 'center', 'valign': 'vcenter'})
            number_format = workbook.add_format(
                {'num_format': '#,##0.00', 'border': 1, 'align': 'center', 'valign': 'vcenter'})

            # Set column widths
            worksheet.set_column('A:A', 15)
            worksheet.set_column('B:B', 15)
            worksheet.set_column('C:C', 15)
            worksheet.set_column('D:D', 15)
            worksheet.set_column('E:E', 15)
            worksheet.set_column('F:F', 15)
            worksheet.set_column('G:G', 20)
            worksheet.set_column('H:H', 20)
            worksheet.set_column('I:I', 20)
            worksheet.set_column('J:J', 15)

            # Add title
            worksheet.merge_range('B1:F1', 'Oman Payslip Report', header_format)

            # Add headers
            headers = ['Employee ID Type', 'Employee ID', 'Reference Number', 'Employee Name', 'Employee BIC', 'IBAN',
                       'Salary Frequency',
                       ' Number of Working days', 'Net Salary', ' Basic Salary','Deductions', ' Extra hours'
                , ' Extra income',' Social Security Deductions']
            worksheet.write_row(3, 1, headers, header_format)

            row = 4
            for payslip in payslip_ids:
                employee_type = payslip.employee_id.employee_type
                employee_id = payslip.employee_id.employee_id or ''
                reference_number = payslip.number or ''
                employee_name = payslip.employee_id.name
                bic = payslip.employee_id.bank_account_id.bank_id.bic or ''
                iban = payslip.employee_id.bank_account_id.acc_number or ''
                salary_frequency = 'Monthly'
                working_days = sum(payslip.worked_days_line_ids.mapped('number_of_days'))
                print(working_days, "workkdddddddddddddddddddd")
                # leaves = sum(
                #     payslip.worked_days_line_ids.filtered(lambda x: x.number_of_days < 0).mapped('number_of_days'))* -1

                basic_salary = sum(payslip.line_ids.filtered(lambda x: x.category_id.code == 'BASIC').mapped('total'))

                allowance = sum(payslip.line_ids.filtered(lambda x: x.category_id.code == 'ALW').mapped('total'))

                deductions = sum(payslip.line_ids.filtered(lambda x: x.category_id.code == 'DED').mapped('total'))
                print(deductions,"rrrrrrrr")

                net_salary = basic_salary + allowance + deductions


                worksheet.write_row(row, 1,
                                    [employee_type, employee_id, reference_number, employee_name, bic, iban,
                                     salary_frequency,working_days, net_salary,basic_salary, deductions],
                                    cell_format)
                row += 1

            worksheet.set_column('B:O', 25, number_format)

        elif country_code == 'AE':

            header_format = workbook.add_format(
                {'bold': True, 'color': 'black', 'font_size': 10, 'align': 'center','bg_color': '#B7B7B7',
                 'valign': 'vcenter'})
            cell_format = workbook.add_format({'font_size': 10, 'border': 1, 'align': 'center', 'valign': 'vcenter'})
            number_format = workbook.add_format(
                {'num_format': '#,##0.00', 'border': 1, 'align': 'center', 'valign': 'vcenter'})

            worksheet.set_column('A:A', 5)
            worksheet.set_column('B:B', 5)
            worksheet.set_column('C:C', 5)
            worksheet.set_column('D:D', 5)
            worksheet.set_column('E:E', 5)

            # Add title
            worksheet.merge_range('B1:F1', 'Dubai Payslip Report', header_format)

            # Add headers
            headers = ['Month', 'Location', 'Employee Name', 'Position', 'Days Worked', 'Leaves', 'Gross Salary',
                       'Allowance', 'Deductions', 'Net Salary', 'Status', 'Payment Mode', 'Bank Name']
            worksheet.write_row(3, 1, headers, header_format)

            row = 4
            for payslip in payslip_ids:
                month = payslip.date_from.strftime('%B')
                location = payslip.employee_id.work_location_id.name or ''
                employee_name = payslip.employee_id.name
                position = payslip.employee_id.job_id.name or ''
                days_worked = sum(payslip.worked_days_line_ids.mapped('number_of_days'))
                leaves = sum(
                    payslip.worked_days_line_ids.filtered(lambda x: x.number_of_days < 0).mapped('number_of_days')) * -1
                basic_salary = sum(payslip.line_ids.filtered(lambda x: x.category_id.code == 'BASIC').mapped('total'))
                gross_salary = sum(payslip.line_ids.filtered(lambda x: x.category_id.code == 'GROSS').mapped('total'))
                allowance = sum(payslip.line_ids.filtered(lambda x: x.category_id.code == 'ALW').mapped('total'))
                deductions = sum(payslip.line_ids.filtered(lambda x: x.category_id.code == 'DED').mapped('total'))
                net_salary = basic_salary + allowance + deductions
                payslip_status = payslip.state
                payment_mode = payslip.employee_id.bank_account_id.bank_id.bic or ''
                bank_name = payslip.employee_id.bank_account_id.bank_id.name or ''



                worksheet.write_row(row, 1,
                                    [month, location, employee_name, position, days_worked, leaves, gross_salary,
                                     allowance, deductions, net_salary,payslip_status,payment_mode,bank_name], cell_format)
                row += 1

            worksheet.set_column('B:N', 25, number_format)

        elif country_code == 'IN':
            header_format = workbook.add_format(
                {'bold': True, 'color': 'black', 'font_size': 10, 'align': 'center', 'valign': 'vcenter',
                 'bg_color': '#C6EFCE'})
            subheader_format = workbook.add_format(
                {'bold': True, 'color': 'black', 'font_size': 10, 'align': 'center', 'valign': 'vcenter',
                 'bg_color': '#F2F2F2'})
            cell_format = workbook.add_format({'font_size': 10, 'border': 1, 'align': 'center', 'valign': 'vcenter'})
            number_format = workbook.add_format(
                {'num_format': '#,##0.00', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
            total_format = workbook.add_format({'bold': True, 'bg_color': '#C6EFCE', 'border': 1, 'align': 'center'})
            current_month_year = datetime.now().strftime('%B - %Y')

            worksheet.set_column('A:A', 5)
            worksheet.set_column('B:B', 10)
            worksheet.set_column('C:C', 10)
            worksheet.set_column('D:D', 20)
            worksheet.set_column('E:E', 20)
            worksheet.set_column('F:F', 10)
            worksheet.set_column('G:G', 20)
            worksheet.set_column('H:L', 15)
            worksheet.set_column('M:M', 20)
            worksheet.set_column('N:N', 15)
            worksheet.set_column('O:O', 15)
            worksheet.set_column('P:P', 15)
            worksheet.set_column('Q:Q', 10)
            worksheet.set_column('R:R', 10)

            headers = [
                'SL NO', 'Emp ID', 'LOP', 'Name', 'Gross Salary (INR)', 'OT/TA', 'Pending Salary Release','DEDUCTION', 'TDS',
                'LOP', 'Salary Advance', 'Prof Tax', 'LATE', 'Arrear paid / Bonus', 'On-Hold', 'Net Payable',
                'Approved By sir', 'Remarks', 'Month days'
            ]

            worksheet.merge_range('D2:K2', f'KLYSTRON_ SALARY CHART FOR THE MONTH OF {current_month_year}',
                                  header_format)

            worksheet.merge_range('A4:A5', 'SL NO', header_format)
            worksheet.merge_range('B4:B5', 'Emp ID', header_format)
            worksheet.merge_range('C4:C5', 'LOP', header_format)
            worksheet.merge_range('D4:D5', 'Name', header_format)
            worksheet.merge_range('E4:E5', 'Gross Salary ', header_format)
            worksheet.merge_range('F4:F5', 'OT/TA', header_format)
            worksheet.merge_range('G4:G5', 'Pending Salary Release', header_format)
            worksheet.merge_range('H4:L4', 'DEDUCTION', header_format)
            worksheet.write('H5', 'TDS', header_format)
            worksheet.write('I5:I5', 'LOP', header_format)
            worksheet.write('J5:J5', 'Salary Advance ', header_format)
            worksheet.write('K5:K5', 'Prof Tax', header_format)
            worksheet.write('L5:L5', 'LATE ', header_format)
            worksheet.merge_range('M4:M5', 'Arrear paid / Bonus ', header_format)
            worksheet.merge_range('N4:N5', 'On-Hold', header_format)
            worksheet.merge_range('O4:O5', 'Net Payable', header_format)
            worksheet.merge_range('P4:P5', 'Approved By sir', header_format)
            worksheet.merge_range('Q4:Q5', 'Remarks ', header_format)
            worksheet.merge_range('R4:R5', 'Month days', header_format)
            # worksheet.write_row('F4', headers[5:], header_format)

            row = 5
            sl_no = 1
            total_gross_salary = 0
            total_net_salary = 0

            for payslip in payslip_ids:
                employee_name = payslip.employee_id.name
                employee_code = payslip.employee_id.employee_id
                gross_salary = sum(payslip.line_ids.filtered(lambda x: x.category_id.code == 'GROSS').mapped('total'))
                allowance = sum(payslip.line_ids.filtered(lambda x: x.category_id.code == 'ALW').mapped('total'))
                deductions = sum(payslip.line_ids.filtered(lambda x: x.category_id.code == 'DED').mapped('total'))
                basic_salary = sum(payslip.line_ids.filtered(lambda x: x.category_id.code == 'BASIC').mapped('total'))
                days_worked = sum(payslip.worked_days_line_ids.mapped('number_of_days'))
                lop = sum(
                    payslip.worked_days_line_ids.filtered(lambda x: x.number_of_days < 0).mapped('number_of_days')) * -1

                ot_ta = sum(payslip.line_ids.filtered(lambda x: x.code == 'OT').mapped('total'))
                pending_salary_release = 0
                tds = sum(
                    payslip.line_ids.filtered(lambda x: x.code == 'TDS').mapped('total'))
                salary_advance = sum(
                    payslip.line_ids.filtered(lambda x: x.code == 'SAR').mapped('total'))
                prof_tax = sum(
                    payslip.line_ids.filtered(lambda x: x.code == 'PROFTAX').mapped('total'))
                late = sum(payslip.line_ids.filtered(lambda x: x.code == 'LATE').mapped('total'))
                arrear_bonus = sum(
                    payslip.line_ids.filtered(lambda x: x.code == 'BONUS').mapped('total'))
                on_hold = 0
                remarks = ''

                net_salary = basic_salary + allowance + deductions
                total_gross_salary += gross_salary
                total_net_salary += net_salary

                current_year = datetime.now().year
                current_month = datetime.now().month

                # Get the number of days in the current month
                month_days = calendar.monthrange(current_year, current_month)[1]

                # Write each field into the respective column
                worksheet.write_row(row, 0, [
                    sl_no, employee_code, lop, employee_name, gross_salary, ot_ta, pending_salary_release,
                    tds, lop, salary_advance, prof_tax, late, arrear_bonus, on_hold, net_salary, 'Approved', remarks, month_days
                ], cell_format)


                row += 1
                sl_no += 1
            print("Total Gross Salary:", total_gross_salary)

            worksheet.write('D20', 'Total', total_format)
            worksheet.write('E20', total_gross_salary, total_format)
            worksheet.write('O20', total_net_salary, total_format)


        workbook.close()
        output.seek(0)
        excel_data = base64.b64encode(output.read())

        attachment = self.env['ir.attachment'].create({
            'name': f'payslip_report_{selected_month}_{selected_year}.xlsx',
            'type': 'binary',
            'datas': excel_data,
            'store_fname': f'payslip_report_{selected_month}_{selected_year}.xlsx',
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'res_model': 'hr.payslip.wps.wizard',
            'res_id': self.id,
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
