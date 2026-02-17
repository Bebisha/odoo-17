# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

import xlwt
import base64
from io import BytesIO
import calendar


class PayrollReportWizard(models.TransientModel):
    _name = 'payroll.report.wizard'
    _description = 'payroll.report.wizard'

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    date_from = fields.Date(string='From Date')
    date_to = fields.Date(string='To Date')
    employee_site = fields.Selection([("crew", "Crew"), ("hq", "HQ")], string='Site', default="hq")
    vessel_id = fields.Many2one('sponsor.sponsor', string="Vessel")

    def _get_data(self):
        """ To get data for the report """
        for rec in self:
            if rec.employee_site == 'hq':
                employees = self.env['hr.employee'].search([('crew', '=', False)])
                employee_list = []
                for employee in employees:
                    payslips = self.env['hr.payslip'].search(
                        [('employee_id', '=', employee.id), ('date_from', '>=', rec.date_from),
                         ('date_to', '<=', self.date_to)])
                    # , ('state', '=', '	paid')
                    worked_days = 0.0
                    paid_leave_days = 0.0
                    unpaid_days = 0.0
                    absent_deduction = 0.0
                    pasi = 0.0
                    earned_days = 0.0
                    day_ot_hrs = 0.0
                    night_ot_hrs = 0.0
                    total_ot_hrs = 0.0
                    total_salary = 0.0
                    prepaid_salaries = 0.0
                    delayed_salaries = 0.0
                    other_deductions = 0.0
                    total_deductions = 0.0
                    net_payslip = 0.0
                    unpaid_amount = 0.0
                    payable_amount = 0.0
                    for pay in payslips:
                        for days in pay.worked_days_line_ids:
                            if days.work_entry_type_id.code == 'WORK100':
                                worked_days += days.number_of_days
                            if days.work_entry_type_id.code == 'LEAVE100' or days.work_entry_type_id.code == 'LEAVE105' or days.work_entry_type_id.code == 'LEAVE110' or days.work_entry_type_id.code == 'LEAVE120':
                                paid_leave_days += days.number_of_days
                            if days.work_entry_type_id.code == 'LEAVE90':
                                unpaid_days += days.number_of_days
                        if unpaid_days > 0:
                            absent_deduction = (
                                                       employee.contract_id.wage + employee.contract_id.housing_allowance + employee.contract_id.travel_allowance) / (
                                                       worked_days * unpaid_days)
                        total_salary = (
                                               employee.contract_id.wage + employee.contract_id.housing_allowance + employee.contract_id.travel_allowance + employee.contract_id.other_allowance + employee.contract_id.extra_income) - (
                                           absent_deduction)
                        net_payslip = total_salary
                        payable_amount = net_payslip
                    if payslips:
                        vals = {
                            'employee': employee.name,
                            'emp_no': employee.employee_no if employee.employee_no else '',
                            'emp_id': employee.employee_id_no if employee.employee_id_no else '',
                            'vessel': employee.sponsor_name if employee.sponsor_name else '',
                            'nationality': employee.country_id.name if employee.country_id else '',
                            'designation': employee.job_id.name if employee.job_id else '',
                            'department': employee.department_id.name if employee.department_id else '',
                            'site': employee.work_location if employee.work_location else '',
                            'worked_days': worked_days,
                            'paid_leave_days': paid_leave_days,
                            'unpaid_days': unpaid_days,
                            'earned_days': earned_days,
                            'basic_per_month': employee.contract_id.wage,
                            'house_allowance': employee.contract_id.housing_allowance,
                            'transport_allowance': employee.contract_id.travel_allowance,
                            'other_allowance': employee.contract_id.other_allowance,
                            'other_income': employee.contract_id.extra_income,
                            'day_ot_hrs': day_ot_hrs,
                            'night_ot_hrs': night_ot_hrs,
                            'total_ot_hrs': total_ot_hrs,
                            'absent_deduction': absent_deduction,
                            'pasi': pasi,
                            'total_salary': total_salary,
                            'prepaid_salaries': prepaid_salaries,
                            'delayed_salaries': delayed_salaries,
                            'other_deductions': other_deductions,
                            'total_deductions': total_deductions,
                            'net_payslip': net_payslip,
                            'unpaid_salaries': unpaid_amount,
                            'payable_amount': payable_amount,
                        }
                        employee_list.append(vals)
                return employee_list
            else:
                employee_list = []
                if not rec.vessel_id:
                    employees = self.env['hr.employee'].search([('crew', '=', True)])
                    for employee in employees:
                        payslips = self.env['hr.payslip'].search(
                            [('employee_id', '=', employee.id), ('date_from', '>=', rec.date_from),
                             ('date_to', '<=', self.date_to)])
                        # , ('state', '=', '	paid')
                        entries = self.env['hr.employee.entry'].search(
                            [('employee_id', '=', employee.id), ('start_date', '>=', rec.date_from),
                             ('end_date', '<=', self.date_to), ('state', '=', 'approved')])
                        salary_pre_payment = self.env['salary.pre.payment'].search(
                            [('employee_id', '=', employee.id), ('paid_date', '>', rec.date_from),
                             ('paid_date', '<', rec.date_to), ('state', '=', 'approved')])
                        at_sea_days = 0.0
                        absence = sum(entries.mapped('absent_days'))
                        earned_days = 0.0
                        ot_hrs = sum(entries.mapped('over_time'))
                        bonus = sum(entries.mapped('bonus'))
                        discharge_1 = sum(entries.mapped('discharge_qty'))
                        prepaid_salaries = sum(salary_pre_payment.mapped('amount'))
                        delayed_salaries = 0.0
                        other_deductions = sum(entries.mapped('shop_deduction'))
                        total_deductions = 0.0
                        unpaid_amount = 0.0
                        total_salary = employee.contract_id.wage + employee.contract_id.other_allowance + employee.contract_id.extra_income + ot_hrs + bonus + discharge_1
                        net_payslip = total_salary - total_deductions
                        payable_amount = net_payslip - unpaid_amount
                        sign_on = fields.Date.to_date(employee.contract_id.date_start).strftime(
                            '%d %b %Y') if employee.contract_id.date_start else 'N/A'
                        sign_off = fields.Date.to_date(employee.contract_id.date_end).strftime(
                            '%d %b %Y') if employee.contract_id.date_end else 'N/A'
                        if payslips:
                            vals = {
                                'employee': employee.name,
                                'emp_no': employee.employee_no if employee.employee_no else '',
                                'emp_id': employee.employee_id_no if employee.employee_id_no else '',
                                'nationality': employee.country_id.name if employee.country_id else '',
                                'designation': employee.job_id.name if employee.job_id else '',
                                'department': employee.department_id.name if employee.department_id else '',
                                'vessel': employee.sponsor_name.name if employee.sponsor_name else '',
                                'sign_on': sign_on,
                                'sign_off': sign_off,
                                'at_sea_days': at_sea_days,
                                'absence': absence,
                                'earned_days': earned_days,
                                'basic_per_day': employee.contract_id.wage,
                                'basic_per_month': employee.contract_id.wage,
                                'other_allowance': employee.contract_id.other_allowance,
                                'other_income': employee.contract_id.extra_income,
                                'ot_hrs': ot_hrs,
                                'bonus': bonus,
                                'discharge_1': discharge_1,
                                'total_salary': total_salary,
                                'pasi': employee.contract_id.pasi_deduction if employee.contract_id.pasi_deduction else 0.0,
                                'prepaid_salaries': prepaid_salaries,
                                'delayed_salaries': delayed_salaries,
                                'other_deductions': other_deductions,
                                'total_deductions': total_deductions,
                                'net_payslip': net_payslip,
                                'unpaid_salaries': unpaid_amount,
                                'payable_amount': payable_amount,
                            }
                            employee_list.append(vals)

                else:
                    employees = self.env['hr.employee'].search(
                        [('crew', '=', True), ('sponsor_name', '=', rec.vessel_id.id)])
                    for employee in employees:
                        payslips = self.env['hr.payslip'].search(
                            [('employee_id', '=', employee.id), ('date_from', '>=', rec.date_from),
                             ('date_to', '<=', self.date_to)])
                        # , ('state', '=', '	paid')
                        entries = self.env['hr.employee.entry'].search(
                            [('employee_id', '=', employee.id), ('start_date', '>=', rec.date_from),
                             ('end_date', '<=', self.date_to), ('state', '=', 'approved')])
                        salary_pre_payment = self.env['salary.pre.payment'].search(
                            [('employee_id', '=', employee.id), ('paid_date', '>', rec.date_from),
                             ('paid_date', '<', rec.date_to), ('state', '=', 'approved')])
                        at_sea_days = 0.0
                        absence = sum(entries.mapped('absent_days'))
                        earned_days = 0.0
                        ot_hrs = sum(entries.mapped('over_time'))
                        bonus = sum(entries.mapped('bonus'))
                        discharge_1 = sum(entries.mapped('discharge_qty'))
                        prepaid_salaries = sum(salary_pre_payment.mapped('amount'))
                        delayed_salaries = 0.0
                        other_deductions = sum(entries.mapped('shop_deduction'))
                        total_deductions = 0.0
                        unpaid_amount = 0.0
                        total_salary = employee.contract_id.wage + employee.contract_id.other_allowance + employee.contract_id.extra_income + ot_hrs + bonus + discharge_1
                        net_payslip = total_salary - total_deductions
                        payable_amount = net_payslip - unpaid_amount
                        sign_on = fields.Date.to_date(employee.contract_id.date_start).strftime(
                            '%d %b %Y') if employee.contract_id.date_start else 'N/A'
                        sign_off = fields.Date.to_date(employee.contract_id.date_end).strftime(
                            '%d %b %Y') if employee.contract_id.date_end else 'N/A'
                        if payslips:
                            vals = {
                                'employee': employee.name,
                                'emp_no': employee.employee_no if employee.employee_no else '',
                                'emp_id': employee.employee_id_no if employee.employee_id_no else '',
                                'nationality': employee.country_id.name if employee.country_id else '',
                                'designation': employee.job_id.name if employee.job_id else '',
                                'department': employee.department_id.name if employee.department_id else '',
                                'vessel': employee.sponsor_name.name if employee.sponsor_name else '',
                                'sign_on': sign_on,
                                'sign_off': sign_off,
                                'at_sea_days': at_sea_days,
                                'absence': absence,
                                'earned_days': earned_days,
                                'basic_per_day': employee.contract_id.wage,
                                'basic_per_month': employee.contract_id.wage,
                                'other_allowance': employee.contract_id.other_allowance,
                                'other_income': employee.contract_id.extra_income,
                                'ot_hrs': ot_hrs,
                                'bonus': bonus,
                                'discharge_1': discharge_1,
                                'total_salary': total_salary,
                                'pasi': employee.contract_id.pasi_deduction if employee.contract_id.pasi_deduction else 0.0,
                                'prepaid_salaries': prepaid_salaries,
                                'delayed_salaries': delayed_salaries,
                                'other_deductions': other_deductions,
                                'total_deductions': total_deductions,
                                'net_payslip': net_payslip,
                                'unpaid_salaries': unpaid_amount,
                                'payable_amount': payable_amount,
                            }
                            employee_list.append(vals)
                return employee_list

    def action_print_pdf(self):
        """ Action to print payroll pdf report """
        employee_list = self._get_data()
        from_date_str = fields.Date.to_date(self.date_from).strftime('%d %B %Y')
        to_date_str = fields.Date.to_date(self.date_to).strftime('%d %B %Y')
        data = {
            'company': self.company_id.name,
            'from': from_date_str,
            'to': to_date_str,
            'employee_list': employee_list
        }
        return self.env.ref('kg_raw_fisheries_payroll_report.action_payroll_report').with_context(
            landscape=True).report_action(self, data=data)

    def action_print_xlsx(self):
        """ Action to print payroll xlsx report """
        employee_list = self._get_data()
        if not employee_list:
            raise ValidationError("There is no data in the selected time period")
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Payroll Report')

        from_date = fields.Date.to_date(self.date_from).strftime('%d %B %Y')
        to_date = fields.Date.to_date(self.date_to).strftime('%d %B %Y')

        bold_font_large = xlwt.Font()
        bold_font_large.bold = True
        bold_font_large.height = 350

        bold_style_large = xlwt.XFStyle()
        bold_style_large.font = bold_font_large
        alignment_large = xlwt.Alignment()
        alignment_large.horz = xlwt.Alignment.HORZ_CENTER
        bold_style_large.alignment = alignment_large

        bold_font_small = xlwt.Font()
        bold_font_small.bold = True
        bold_font_small.height = 220

        bold_style_small = xlwt.XFStyle()
        bold_style_small.font = bold_font_small
        alignment_small = xlwt.Alignment()
        alignment_small.horz = xlwt.Alignment.HORZ_CENTER
        bold_style_small.alignment = alignment_small

        row_height = 30
        worksheet.row(6).set_style(xlwt.easyxf(f'font: height {row_height * 20};'))
        # line.description if line.description else ' '

        worksheet.write_merge(0, 1, 4, 8, 'Payroll Report', bold_style_large)
        worksheet.write_merge(3, 3, 1, 3, f'From: {from_date}', bold_style_small)
        worksheet.write_merge(3, 3, 13, 15, f'To: {to_date}', bold_style_small)
        if self.employee_site == 'hq':
            worksheet.write(6, 0, 'No.', bold_style_small)
            worksheet.write(6, 1, 'Emp No.', bold_style_small)
            worksheet.write_merge(6, 6, 2, 5, 'Name', bold_style_small)
            worksheet.write(6, 6, 'ID.', bold_style_small)
            worksheet.write_merge(6, 6, 7, 8, 'Nationality', bold_style_small)
            worksheet.write_merge(6, 6, 9, 10, 'Designation/Rank', bold_style_small)
            worksheet.write_merge(6, 6, 11, 12, 'Department', bold_style_small)
            worksheet.write(6, 13, 'Site', bold_style_small)
            worksheet.write_merge(6, 6, 14, 15, 'No. of Worked Days', bold_style_small)
            worksheet.write_merge(6, 6, 16, 17, 'Leaves Taken', bold_style_small)
            worksheet.write_merge(6, 6, 18, 19, 'Absent Days(Unpaid Leaves)', bold_style_small)
            worksheet.write_merge(6, 6, 20, 21, 'Earned Days', bold_style_small)
            worksheet.write_merge(6, 6, 22, 23, 'Basic Per Month', bold_style_small)
            worksheet.write_merge(6, 6, 24, 25, 'Housing Allowance', bold_style_small)
            worksheet.write_merge(6, 6, 26, 27, 'Transport Allowance', bold_style_small)
            worksheet.write_merge(6, 6, 28, 29, 'Other Allowance', bold_style_small)
            worksheet.write_merge(6, 6, 30, 31, 'Other Income', bold_style_small)
            worksheet.write_merge(5, 5, 24, 31, 'Allowances', bold_style_small)
            worksheet.write(6, 32, 'Day Time Hrs', bold_style_small)
            worksheet.write(6, 33, 'Night Time Hrs', bold_style_small)
            worksheet.write(6, 34, 'Total OT USD', bold_style_small)
            worksheet.write_merge(5, 5, 32, 34, 'OT', bold_style_small)
            worksheet.write(6, 35, 'Absent Deduction', bold_style_small)
            worksheet.write(6, 36, 'PASI', bold_style_small)
            worksheet.write_merge(6, 6, 37, 38, 'Total Salary', bold_style_small)
            worksheet.write(6, 39, 'Prepaid Salaries', bold_style_small)
            worksheet.write_merge(6, 6, 40, 41, 'Delayed Salaries 30%', bold_style_small)
            worksheet.write(6, 42, 'Other Deductions', bold_style_small)
            worksheet.write(6, 43, 'Total Deductions', bold_style_small)
            worksheet.write(6, 44, 'Net Payslip', bold_style_small)
            worksheet.write(6, 45, 'Unpaid Salaries', bold_style_small)
            worksheet.write_merge(6, 6, 46, 47, 'For Payment(Payable)', bold_style_small)

            for row, employee in enumerate(employee_list, start=7):
                worksheet.write(row, 0, row - 6)
                worksheet.write(row, 1, employee.get('emp_no', ''))
                worksheet.write_merge(row, row, 2, 5, employee['employee'])
                worksheet.write(row, 6, employee.get('emp_id', ''))
                worksheet.write_merge(row, row, 7, 8, employee['nationality'])
                worksheet.write_merge(row, row, 9, 10, employee['designation'])
                worksheet.write_merge(row, row, 11, 12, employee['department'])
                worksheet.write(row, 13, employee.get('site', ''))
                worksheet.write_merge(row, row, 14, 15, employee['worked_days'])
                worksheet.write_merge(row, row, 16, 17, employee['paid_leave_days'])
                worksheet.write_merge(row, row, 18, 19, employee['unpaid_days'])
                worksheet.write_merge(row, row, 20, 21, employee['earned_days'])
                worksheet.write_merge(row, row, 22, 23, employee['basic_per_month'])
                worksheet.write_merge(row, row, 24, 25, employee['house_allowance'])
                worksheet.write_merge(row, row, 26, 27, employee['transport_allowance'])
                worksheet.write_merge(row, row, 28, 29, employee['other_allowance'])
                worksheet.write_merge(row, row, 30, 31, employee['other_income'])
                worksheet.write(row, 32, employee['day_ot_hrs'])
                worksheet.write(row, 33, employee['night_ot_hrs'])
                worksheet.write(row, 34, employee['total_ot_hrs'])
                worksheet.write(row, 35, employee['absent_deduction'])
                worksheet.write(row, 36, employee['pasi'])
                worksheet.write_merge(row, row, 37, 38, employee['total_salary'])
                worksheet.write(row, 39, employee['prepaid_salaries'])
                worksheet.write_merge(row, row, 40, 41, employee['delayed_salaries'])
                worksheet.write(row, 42, employee['other_deductions'])
                worksheet.write(row, 43, employee['total_deductions'])
                worksheet.write(row, 44, employee['net_payslip'])
                worksheet.write(row, 45, employee['unpaid_salaries'])
                worksheet.write_merge(row, row, 46, 47, employee['payable_amount'])
        else:
            worksheet.write(6, 0, 'No.', bold_style_small)
            worksheet.write(6, 1, 'Emp No.', bold_style_small)
            worksheet.write_merge(6, 6, 2, 5, 'Name', bold_style_small)
            worksheet.write(6, 6, 'ID.', bold_style_small)
            worksheet.write_merge(6, 6, 7, 8, 'Nationality', bold_style_small)
            worksheet.write_merge(6, 6, 9, 10, 'Designation/Rank', bold_style_small)
            worksheet.write_merge(6, 6, 11, 12, 'Department', bold_style_small)
            worksheet.write(6, 13, 'Vessel Name', bold_style_small)
            worksheet.write(6, 14, 'Sign On', bold_style_small)
            worksheet.write(6, 15, 'Sign Off', bold_style_small)
            worksheet.write(6, 16, 'At Sea Days', bold_style_small)
            worksheet.write(6, 17, 'Absence', bold_style_small)
            worksheet.write(6, 18, 'Earned', bold_style_small)
            worksheet.write(6, 19, 'Basic Per Day', bold_style_small)
            worksheet.write(6, 20, 'Basic Per Month', bold_style_small)
            worksheet.write_merge(5, 5, 21, 23, 'Basic', bold_style_small)
            worksheet.write_merge(6, 6, 21, 23, 'Salaries/ Expats/ Contract', bold_style_small)
            worksheet.write_merge(5, 5, 24, 26, 'Basic', bold_style_small)
            worksheet.write_merge(6, 6, 24, 26, 'Salaries/ Expats/ Contract', bold_style_small)
            worksheet.write(6, 27, 'Other Allowance', bold_style_small)
            worksheet.write(6, 28, 'Other Income', bold_style_small)
            worksheet.write(6, 29, 'OT', bold_style_small)
            worksheet.write(6, 30, 'Bonus', bold_style_small)
            worksheet.write(6, 31, 'Discharging Allowance', bold_style_small)
            # worksheet.write(6, 32, 'Discharging 2', bold_style_small)
            # worksheet.write(6, 33, 'Discharging 3', bold_style_small)
            # worksheet.write_merge(6, 6, 34, 36, 'Total Discharging Allowance(15 USD per Ton)', bold_style_small)
            worksheet.write_merge(6, 6, 32, 34, 'Total Salary/ Expats/ Contract', bold_style_small)
            worksheet.write(6, 35, 'Pasi', bold_style_small)
            worksheet.write(6, 36, 'Prepaid Salaries', bold_style_small)
            worksheet.write(6, 37, 'Delayed Salaries', bold_style_small)
            worksheet.write(6, 38, 'Other Deductions', bold_style_small)
            worksheet.write(6, 39, 'Total Deductions', bold_style_small)
            worksheet.write(6, 40, 'Net Payslip', bold_style_small)
            worksheet.write(6, 41, 'Unpaid Salaries', bold_style_small)
            worksheet.write_merge(6, 6, 42, 44, 'For Payment(Payable)', bold_style_small)

            for row, employee in enumerate(employee_list, start=7):
                worksheet.write(row, 0, row - 6)
                worksheet.write(row, 1, employee.get('emp_no', ''))
                worksheet.write_merge(row, row, 2, 5, employee['employee'])
                worksheet.write(row, 6, employee.get('emp_id', ''))
                worksheet.write_merge(row, row, 7, 8, employee['nationality'])
                worksheet.write_merge(row, row, 9, 10, employee['designation'])
                worksheet.write_merge(row, row, 11, 12, employee['department'])
                worksheet.write(row, 13, employee.get('vessel', ''))
                worksheet.write(row, 14, employee['sign_on'])
                worksheet.write(row, 15, employee['sign_off'])
                worksheet.write(row, 16, employee['at_sea_days'])
                worksheet.write(row, 17, employee['absence'])
                worksheet.write(row, 18, employee['earned_days'])
                worksheet.write(row, 19, employee['basic_per_day'])
                worksheet.write(row, 20, employee['basic_per_month'])
                # worksheet.write_merge(row, row, 21, 23, employee['department'])
                # worksheet.write_merge(row, row, 24, 26, employee['department'])
                worksheet.write(row, 27, employee['other_allowance'])
                worksheet.write(row, 28, employee['other_income'])
                worksheet.write(row, 29, employee['ot_hrs'])
                worksheet.write(row, 30, employee['bonus'])
                worksheet.write(row, 31, employee['discharge_1'])
                # worksheet.write(row, 32, employee['discharge_2'])
                # worksheet.write(row, 33, employee['discharge_3'])
                # worksheet.write_merge(row, row, 34, 36, employee['total_discharge'])
                worksheet.write_merge(row, row, 32, 34, employee['total_salary'])
                worksheet.write(row, 35, employee['pasi'])
                worksheet.write(row, 36, employee['prepaid_salaries'])
                worksheet.write(row, 37, employee['delayed_salaries'])
                worksheet.write(row, 38, employee['other_deductions'])
                worksheet.write(row, 39, employee['total_deductions'])
                worksheet.write(row, 40, employee['net_payslip'])
                worksheet.write(row, 41, employee['unpaid_salaries'])
                worksheet.write_merge(row, row, 42, 44, employee['payable_amount'])
        output = BytesIO()
        workbook.save(output)
        output.seek(0)
        attachment = self.env['ir.attachment'].create({
            'name': 'Payroll_Report.xls',
            'type': 'binary',
            'datas': base64.b64encode(output.getvalue()),
            'res_model': self._name,
            'res_id': self.id,
        })
        vals = {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'employee_site': self.employee_site,
            'vessel_id': self.vessel_id.id if self.vessel_id else None,
            'attachment_id': attachment.id
        }
        self.env['payroll.report.approval'].create(vals)
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
