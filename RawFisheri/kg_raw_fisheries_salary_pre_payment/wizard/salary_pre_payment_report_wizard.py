# -*- coding: utf-8 -*-
import base64
from io import BytesIO

import xlwt

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.release import description


class EntryReportWizard(models.TransientModel):
    _name = 'salary.pre.payment.report.wizard'
    _description = 'salary.pre.payment.report.wizard'

    date_from = fields.Date(string='From')
    date_to = fields.Date(string='To')
    vessel_id = fields.Many2one('sponsor.sponsor', string='Vessel')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    def get_data(self):
        """ Function to get data for the report """
        for rec in self:
            payment_list = []
            if rec.vessel_id:
                employees = self.env['hr.employee'].search(
                    [('crew', '=', True), ('sponsor_name', '=', rec.vessel_id.id)])
                for employee in employees:
                    entries = self.env['salary.pre.payment'].search(
                        [('employee_id', '=', employee.id), ('paid_date', '>=', rec.date_from),
                         ('paid_date', '<=', rec.date_to), ('state', '=', 'approved')])

                    if entries:
                        amount = sum(entries.mapped('amount'))
                        paid_date = entries.mapped('paid_date')
                        description = entries.mapped('name')
                        currency = entries.mapped('currency_id.name')
                        entry = {
                            'employee': employee.name,
                            'vessel': employee.sponsor_name.name,
                            'amount': amount,
                            'paid_date': paid_date,
                            'description': description,
                            'currency': currency,
                        }
                        payment_list.append(entry)

            else:
                employees = self.env['hr.employee'].search([('crew', '=', True)])
                for employee in employees:
                    entries = self.env['salary.pre.payment'].search(
                        [('employee_id', '=', employee.id), ('paid_date', '>=', rec.date_from),
                         ('paid_date', '<=', rec.date_to), ('state', '=', 'approved')])

                    if entries:
                        amount = sum(entries.mapped('amount'))
                        paid_date = entries.mapped('paid_date')
                        description = entries.mapped('name')
                        currency = entries.mapped('currency_id.name')
                        entry = {
                            'employee': employee.name,
                            'vessel': employee.sponsor_name.name,
                            'amount': amount,
                            'paid_date': paid_date,
                            'description': description if description else '',
                            'currency': currency,
                        }
                        payment_list.append(entry)
            return payment_list

    def action_print_pdf(self):
        """ Action to print the pdf report """
        payment_list = self.get_data()
        if not payment_list:
            raise ValidationError("There is no data in the selected time period!")
        data = {
            'company': self.company_id,
            'company_name': self.company_id.name,
            'from': self.date_from,
            'to': self.date_to,
            'payment_list': payment_list,
        }
        return self.env.ref('kg_raw_fisheries_salary_pre_payment.action_salary_pre_payment_report'
                            '').with_context(
            landscape=True).report_action(self, data=data)

    def action_print_xlsx(self):
        """ Action to print the excel report """
        payment_list = self.get_data()
        if not payment_list:
            raise ValidationError("There is no data in the selected time period!")
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

        worksheet.write_merge(0, 1, 4, 8, 'Salary Pre Payment Report', bold_style_large)
        worksheet.write_merge(3, 3, 1, 3, f'From: {from_date}', bold_style_small)
        worksheet.write_merge(3, 3, 13, 15, f'To: {to_date}', bold_style_small)
        worksheet.write(6, 0, 'No.', bold_style_small)
        worksheet.write_merge(6, 6, 1, 4, 'Employee', bold_style_small)
        worksheet.write_merge(6, 6, 5, 7, 'Vessel', bold_style_small)
        worksheet.write(6, 8, 'Paid Date', bold_style_small)
        worksheet.write_merge(6, 6, 9, 13, 'Description', bold_style_small)
        worksheet.write_merge(6, 6, 14, 15, 'Advance Amount', bold_style_small)
        worksheet.write(6, 16, 'Currency', bold_style_small)

        for row, payment in enumerate(payment_list, start=7):
            worksheet.write(row, 0, row - 6)
            worksheet.write_merge(row, row, 1, 4, payment.get('employee', ''))
            worksheet.write_merge(row, row, 5, 7, payment['vessel'])
            worksheet.write(row, 8, payment['paid_date'][0].strftime('%d-%m-%Y'))
            worksheet.write_merge(row, row, 9, 13, payment['description'][0])
            worksheet.write_merge(row, row, 14, 15, payment['amount'])
            worksheet.write(row, 16, payment['currency'])

        output = BytesIO()
        workbook.save(output)
        output.seek(0)
        attachment = self.env['ir.attachment'].create({
            'name': 'Entries_Report.xls',
            'type': 'binary',
            'datas': base64.b64encode(output.getvalue()),
            'res_model': self._name,
            'res_id': self.id,
        })
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
