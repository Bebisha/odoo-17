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
    _name = "payslip.report.wizard"
    _description = "Payroll report"

    date_from = fields.Date()
    date_to = fields.Date()
    actual_deduction = fields.Boolean('Actual')
    expact_wiz = fields.Boolean('Expact')
    fileout = fields.Binary('File', readonly=True)
    fileout_filename = fields.Char('Filename', readonly=True)

    def print_sif_xlsx(self):

        if self.date_from > self.date_to:
            raise ValidationError(_('Start Date must be less than End Date'))

        if self.date_from and self.date_to:
            if self.date_from.month != self.date_to.month:
                raise UserError(_('The Payslip of the same month will be printed'))

        """ button action to print xlsx report of non UAE customers"""

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
        datetime_string = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_name = 'PaySlip Report'
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

        amt = workbook.add_format({"num_format": "0.00", 'font_size': '10px', 'align': 'right'})
        sl_no = workbook.add_format({'font_size': '10px', 'align': 'center'})

        bold = workbook.add_format({'bold': True, 'font_size': '8px', 'align': 'center'})
        bold_total = workbook.add_format({'bold': True, 'font_size': '10px', 'align': 'center'})
        bold_total_amount = workbook.add_format(
            {"num_format": "0.00", 'bold': True, 'font_size': '10px', 'align': 'right'})

        row = 0
        col = 0
        payslip_obj = self.env['hr.payslip'].search(
            [('date_from', '>=', self.date_from), ('date_to', '<=', self.date_to),('state','=','done')])
        payslip_lines = payslip_obj.mapped('line_ids')
        allowances = payslip_lines.filtered(lambda l: l.category_id.code == 'ALW').mapped(
            'name')
        deductions = payslip_lines.filtered(lambda l: l.category_id.code == 'DED').mapped(
            'name')
        basic = payslip_lines.filtered(lambda l: l.category_id.code == 'BASIC').mapped(
            'name')
        unique_basic = list(OrderedDict.fromkeys(basic))
        unique_allowances = list(OrderedDict.fromkeys(allowances))
        unique_deductions = list(OrderedDict.fromkeys(deductions))
        sheet.merge_range(row, col, row + 1,
                          col + len(unique_basic) + len(unique_allowances) + len(unique_deductions) + 7,
                          'Payroll Report', head)
        sheet.merge_range(row + 2, col, row + 2, col + 2, 'Date Range:', bold)
        sheet.merge_range(row + 2, col + 3, row + 2, col + 5,
                          '%s - %s ' % (self.date_from.strftime('%d-%m-%Y'), self.date_to.strftime('%d-%m-%Y')),
                          date_style)
        sheet.set_column(row, col, 8)
        sheet.set_column(row + 1, col + 1, 25)
        sheet.set_column(row + 2, col + 2, 15)
        sheet.set_column(row + 3, col + 3, 20)
        sheet.set_row(row + 2, 30)
        sheet.set_row(row + 3, 30)
        # sheet.write(row + 3, col, 'SL. No.', bold)
        # sheet.write(row + 3, col + 1, 'Dept', bold)
        # sheet.write(row + 3, col + 2, 'Emp.No', bold)
        # sheet.write(row + 3, col + 3, 'Staff Name', bold)
        # sheet.write(row + 3, col + 4, 'Position', bold)
        # sheet.write(row + 3, col + 5, 'Salary Days', bold)
        # sheet.set_column(row + 4, col + 4, 25)
        # sheet.set_column(row + 5, col + 5, 10)
        #
        # for basic_name in unique_basic:
        #     sheet.write(row + 3, col + 6, basic_name, bold)
        #     col += 1
        # for alw in unique_allowances:
        #     sheet.write(row + 3, col + 6, alw, bold)
        #     col += 1
        # sheet.write(row + 3, col + 6, 'Gross', bold)
        # for ded in unique_deductions:
        #     sheet.write(row + 3, col + 7, ded, bold)
        #     col += 1
        # sheet.write(row + 3, col + 7, 'Net Salary', bold)
        #
        sheet.set_column(4, 4, 20)
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
        # row = 4
        # col = 0
        new_col = col
        #
        total_amount = 0
        # for paysl in payslip_obj:
        #     sheet.write(row, col, count, sl_no)
        #     sheet.write(row, col + 1, paysl.employee_id.department_id.name or '', txt)
        #     sheet.write(row, col + 2, paysl.employee_id.registration_number or '', txt)
        #     sheet.write(row, col + 3, paysl.employee_id.name, txt)
        #     sheet.write(row, col + 4, paysl.employee_id.job_id.name or '', txt)
        #     sheet.write(row, col + 5, 30 or '', txt)
        #     basic_amount = 0
        #     for basic_name in unique_basic:
        #         basic = sum(paysl.line_ids.filtered(lambda x: x.name == str(basic_name)).mapped('total'))
        #         sheet.write(row, col + 6, basic or '0', amt)
        #         basic_amount += basic
        #         col += 1
        #     gross = basic_amount
        #     net = 0
        #     ded_amt = 0
        #     for alw_name in unique_allowances:
        #         alw = sum(paysl.line_ids.filtered(lambda x: x.name == alw_name).mapped('total'))
        #         sheet.write(row, col + 6, alw or '0', amt)
        #         gross += alw
        #         col += 1
        #     sheet.write(row, col + 6, gross or '0', amt)
        #     for ded_name in unique_deductions:
        #         ded = sum(paysl.line_ids.filtered(lambda x: x.name == ded_name).mapped('total'))
        #         ded_amt += ded
        #         sheet.write(row, col + 7, ded or '0', amt)
        #         col += 1
        #     net = gross + ded_amt
        #     sheet.write(row, col + 7, net or '0', amt)
        #     total_amount += net
        #     row += 1
        #     new_col = col
        #     col = 0
        #     count += 1
        #
        # hr_id = self.env['ir.config_parameter'].sudo().get_param('kg_hr.hr_id', default=False)
        # finance_id = self.env['ir.config_parameter'].sudo().get_param('kg_hr.finance_id', default=False)
        # ceo_id = self.env['ir.config_parameter'].sudo().get_param('kg_hr.ceo_id', default=False)
        # ceo = self.env['hr.employee'].browse(int(ceo_id))
        # finance = self.env['hr.employee'].browse(int(finance_id))
        # hr = self.env['hr.employee'].browse(int(hr_id))
        # sheet.write(row + 1, new_col + 6,
        #             'TOTAL AMOUNT', bold_total)
        # sheet.write(row + 1, new_col + 7, total_amount, bold_total_amount)
        # sheet.write('A' + str(row + 3), 'PREPARED BY', bold_total)
        # sheet.write('A' + str(row + 4), self.env.user.name, txt)
        # sheet.write('D' + str(row + 3), 'HR', bold_total)
        # sheet.write('D' + str(row + 4), hr.name or ' ', txt)
        # sheet.write('G' + str(row + 3), 'FINANCE', bold_total)
        # sheet.write('G' + str(row + 4), finance.name or '', txt)
        # sheet.write('J' + str(row + 3), 'CEO', bold_total)
        # sheet.write('J' + str(row + 4), ceo.name or '', txt)

        sheet.write(row + 3, col, 'SL. No.', bold)
        sheet.write(row + 3, col + 1, 'Name of the Employee', bold)
        sheet.write(row + 3, col + 2, 'Emp ID', bold)
        sheet.write(row + 3, col + 3, 'DOJ', bold)
        sheet.write(row + 3, col + 4, 'Basic', bold)
        sheet.write(row + 3, col + 5, 'Over Time rate', bold)
        sheet.write(row + 3, col + 6, 'Over Time hours', bold)
        sheet.write(row + 3, col + 7, 'Over Time amount ', bold)
        sheet.write(row + 3, col + 8, 'Food Allowance  ', bold)
        sheet.write(row + 3, col + 9, 'House Rent Allowance', bold)
        sheet.write(row + 3, col + 10, 'Travel Allowance ', bold)
        sheet.write(row + 3, col + 11, 'Advance', bold)
        sheet.write(row + 3, col + 12, 'Bonus/ Incentive', bold)
        sheet.write(row + 3, col + 13, 'Others', bold)
        sheet.write(row + 3, col + 14, 'Gross salary Payable', bold)
        sheet.write(row + 3, col + 15, 'D: Non-working Days', bold)
        sheet.write(row + 3, col + 16, 'D: Advances', bold)
        sheet.write(row + 3, col + 17, 'D: Telephone', bold)
        sheet.write(row + 3, col + 18, 'D: Security Deposit', bold)
        sheet.write(row + 3, col + 19, 'D: Others', bold)
        sheet.write(row + 3, col + 20, 'Total Deductions', bold)
        sheet.write(row + 3, col + 21, 'Net Payable', bold)
        sheet.write(row + 3, col + 22, 'Net Payable (Adjusted)', bold)
        row = 4
        col = 0
        total_basic = 0
        total_overtime_hr = 0
        total_overtime_amount = 0
        total_food_allowance_amount = 0
        total_house_allowance_amount = 0
        total_travel_allowance_amount = 0
        total_advance_allowance_amount = 0
        total_bonus_allowance_amount = 0
        total_other_allowance_amount = 0
        total_gross = 0
        total_dnwd = 0
        total_do = 0
        total_dt = 0
        total_da = 0
        total_dsd = 0
        total_deduction = 0
        total_net = 0
        total_net_round = 0
        for paysl in payslip_obj:
            doj = paysl.employee_id.join_date
            if doj:
                doj = paysl.employee_id.join_date.strftime('%d/%m/%Y')
            sheet.write(row, col, count, sl_no)
            sheet.write(row, col + 1, paysl.employee_id.name or '', txt)
            sheet.write(row, col + 2, paysl.employee_id.registration_number or '', txt)
            sheet.write(row, col + 3, doj or '', txt)
            # sheet.write(row, col + 4, paysl.employee_id.job_id.name or '', txt)
            basic = sum(paysl.line_ids.filtered(lambda x: x.salary_rule_id.code == 'BASIC').mapped('total'))
            food_allowance = sum(paysl.line_ids.filtered(lambda x: x.salary_rule_id.code == 'FA').mapped('total'))
            house_allowance = sum(paysl.line_ids.filtered(lambda x: x.salary_rule_id.code == 'HRA').mapped('total'))
            travel_allowance = sum(paysl.line_ids.filtered(lambda x: x.salary_rule_id.code == 'TA').mapped('total'))
            advance_allowance = sum(paysl.line_ids.filtered(lambda x: x.salary_rule_id.code == 'AA').mapped('total'))
            bonus_allowance = sum(paysl.line_ids.filtered(lambda x: x.salary_rule_id.code == 'BA').mapped('total'))
            other_allowance = sum(paysl.line_ids.filtered(lambda x: x.salary_rule_id.code == 'OTA').mapped('total'))
            allowance = food_allowance + house_allowance + travel_allowance + advance_allowance + bonus_allowance + other_allowance
            dnwd = sum(paysl.line_ids.filtered(lambda x: x.salary_rule_id.code == 'DNWD').mapped('total'))
            da = sum(paysl.line_ids.filtered(lambda x: x.salary_rule_id.code == 'DA').mapped('total'))
            dt = sum(paysl.line_ids.filtered(lambda x: x.salary_rule_id.code == 'DT').mapped('total'))
            dsd = sum(paysl.line_ids.filtered(lambda x: x.salary_rule_id.code == 'DSD').mapped('total'))
            do = sum(paysl.line_ids.filtered(lambda x: x.salary_rule_id.code == 'DO').mapped('total'))
            gross = basic + allowance
            deductions = dnwd + da + dt + dsd + do
            total_deduction += deductions
            total_basic += basic
            total_overtime_hr += paysl.overtime_hours
            total_overtime_amount += (paysl.overtime_hours * paysl.overtime_amount)
            total_food_allowance_amount += food_allowance
            total_house_allowance_amount += house_allowance
            total_travel_allowance_amount += travel_allowance
            total_advance_allowance_amount += advance_allowance
            total_bonus_allowance_amount += bonus_allowance
            total_other_allowance_amount += other_allowance
            total_gross += gross
            total_da += da
            total_do += do
            total_dt += dt
            total_dsd += dsd
            total_dnwd += dnwd
            total_net += (gross + deductions)
            total_net_round += round(gross + deductions, 0)
            sheet.write(row, col + 4, basic or '0', amt)

            sheet.write(row, col + 5, paysl.overtime_amount or ' ', amt)
            sheet.write(row, col + 6, paysl.overtime_hours or ' ', amt)
            sheet.write(row, col + 7, paysl.overtime_hours * paysl.overtime_amount or ' ', amt)
            sheet.write(row, col + 8, food_allowance or ' ', amt)
            sheet.write(row, col + 9, house_allowance or ' ', amt)
            sheet.write(row, col + 10, travel_allowance or ' ', amt)
            sheet.write(row, col + 11, advance_allowance or ' ', amt)
            sheet.write(row, col + 12, bonus_allowance or ' ', amt)
            sheet.write(row, col + 13, other_allowance or ' ', amt)
            sheet.write(row, col + 14, gross or ' ', amt)
            sheet.write(row, col + 15, dnwd or ' ', amt)
            sheet.write(row, col + 16, da or ' ', amt)
            sheet.write(row, col + 17, dt or ' ', amt)
            sheet.write(row, col + 18, dsd or ' ', amt)
            sheet.write(row, col + 19, do or ' ', amt)
            sheet.write(row, col + 20, deductions or ' ', amt)
            sheet.write(row, col + 21, gross + deductions or ' ', amt)
            sheet.write(row, col + 22, round(gross + deductions, 0) or ' ', amt)

            count += 1
            row += 1
        sheet.merge_range(row, col, row, col + 3, 'Gross Total', bold_total)
        sheet.write(row, col + 4, total_basic or ' ', bold_total_amount)
        sheet.write(row, col + 6, total_overtime_hr or ' ', bold_total_amount)
        sheet.write(row, col + 7, total_overtime_amount or ' ', bold_total_amount)
        sheet.write(row, col + 8, total_food_allowance_amount or ' ', bold_total_amount)
        sheet.write(row, col + 9, total_house_allowance_amount or ' ', bold_total_amount)
        sheet.write(row, col + 10, total_travel_allowance_amount or ' ', bold_total_amount)
        sheet.write(row, col + 11, total_advance_allowance_amount or ' ', bold_total_amount)
        sheet.write(row, col + 12, total_bonus_allowance_amount or ' ', bold_total_amount)
        sheet.write(row, col + 13, total_other_allowance_amount or ' ', bold_total_amount)
        sheet.write(row, col + 14, total_gross or ' ', bold_total_amount)
        sheet.write(row, col + 15, total_dnwd or ' ', bold_total_amount)
        sheet.write(row, col + 16, total_da or ' ', bold_total_amount)
        sheet.write(row, col + 17, total_dt or ' ', bold_total_amount)
        sheet.write(row, col + 18, total_dsd or ' ', bold_total_amount)
        sheet.write(row, col + 19, total_do or ' ', bold_total_amount)
        sheet.write(row, col + 20, total_deduction or ' ', bold_total_amount)
        sheet.write(row, col + 21, total_net or ' ', bold_total_amount)
        sheet.write(row, col + 22, total_net_round or ' ', bold_total_amount)

        # hr_id = self.env['ir.config_parameter'].sudo().get_param('kg_hr.hr_id', default=False)
        # finance_id = self.env['ir.config_parameter'].sudo().get_param('kg_hr.finance_id', default=False)
        # ceo_id = self.env['ir.config_parameter'].sudo().get_param('kg_hr.ceo_id', default=False)
        # ceo = self.env['hr.employee'].browse(int(ceo_id))
        # finance = self.env['hr.employee'].browse(int(finance_id))
        # hr = self.env['hr.employee'].browse(int(hr_id))
        # sheet.write(row + 1, new_col + 6,
        #             'TOTAL AMOUNT', bold_total)
        # sheet.write(row + 1, new_col + 7, total_amount, bold_total_amount)
        # sheet.write('A' + str(row + 3), 'PREPARED BY', bold_total)
        # sheet.write('A' + str(row + 4), self.env.user.name, txt)
        # sheet.write('D' + str(row + 3), 'HR', bold_total)
        # sheet.write('D' + str(row + 4), hr.name or ' ', txt)
        # sheet.write('G' + str(row + 3), 'FINANCE', bold_total)
        # sheet.write('G' + str(row + 4), finance.name or '', txt)
        # sheet.write('J' + str(row + 3), 'CEO', bold_total)
        # sheet.write('J' + str(row + 4), ceo.name or '', txt)
        workbook.close()
