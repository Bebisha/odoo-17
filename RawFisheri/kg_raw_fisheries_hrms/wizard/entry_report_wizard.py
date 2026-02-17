# -*- coding: utf-8 -*-
import base64
from io import BytesIO

import xlwt

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class EntryReportWizard(models.TransientModel):
    _name = 'entry.report.wizard'
    _description = 'entry.report.wizard'

    date_from = fields.Date(string='From')
    date_to = fields.Date(string='To')
    vessel_id = fields.Many2one('sponsor.sponsor', string='Vessel')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    def get_data(self):
        """ Function to get data for the report """
        for rec in self:
            entry_list = []
            if rec.vessel_id:
                employees = self.env['hr.employee'].search(
                    [('crew', '=', True), ('sponsor_name', '=', rec.vessel_id.id)])
                for employee in employees:
                    entries = self.env['hr.employee.entry'].search(
                        [('employee_id', '=', employee.id), ('start_date', '>=', rec.date_from),
                         ('end_date', '<=', rec.date_to)])

                    if entries:
                        ot = sum(entries.mapped('over_time'))
                        bonus = sum(entries.mapped('bonus'))
                        duration = sum(entries.mapped('duration'))
                        absent_days = sum(entries.mapped('absent_days'))
                        discharge = sum(entries.mapped('discharge_qty'))
                        shop_deduction = sum(entries.mapped('shop_deduction'))
                        travelling_days = sum(entries.mapped('travelling_days'))

                        entry = {
                            'employee': employee.name,
                            'vessel': employee.sponsor_name.name,
                            'ot': ot,
                            'bonus': bonus,
                            'duration': duration,
                            'absent_days': absent_days,
                            'discharge': discharge,
                            'shop_deduction': shop_deduction,
                            'travelling_days': travelling_days
                        }
                        entry_list.append(entry)

            else:
                employees = self.env['hr.employee'].search([('crew', '=', True)])
                for employee in employees:
                    entries = self.env['hr.employee.entry'].search(
                        [('employee_id', '=', employee.id), ('start_date', '>=', rec.date_from),
                         ('end_date', '<=', rec.date_to)])

                    if entries:
                        ot = sum(entries.mapped('over_time'))
                        bonus = sum(entries.mapped('bonus'))
                        duration = sum(entries.mapped('duration'))
                        absent_days = sum(entries.mapped('absent_days'))
                        discharge = sum(entries.mapped('discharge_qty'))
                        shop_deduction = sum(entries.mapped('shop_deduction'))
                        travelling_days = sum(entries.mapped('travelling_days'))

                        entry = {
                            'employee': employee.name,
                            'vessel': employee.sponsor_name.name,
                            'ot': ot,
                            'bonus': bonus,
                            'duration': duration,
                            'absent_days': absent_days,
                            'discharge': discharge,
                            'shop_deduction': shop_deduction,
                            'travelling_days': travelling_days
                        }
                        entry_list.append(entry)
            return entry_list

    def action_print_pdf(self):
        """ Action to print the pdf report """
        entry_list = self.get_data()
        if not entry_list:
            raise ValidationError("There is no data in the selected time period!")
        data = {
            'company': self.company_id.logo,
            'company_name': self.company_id.name,
            'from': self.date_from,
            'to': self.date_to,
            'entry_list': entry_list,
        }
        return self.env.ref('kg_raw_fisheries_hrms.action_employee_entries_report').with_context(
            landscape=True).report_action(self, data=data)

    def action_print_xlsx(self):
        """ Action to print excel report """
        entry_list = self.get_data()
        if not entry_list:
            raise ValidationError("There is no data in the selected time period!")
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Employee Entry Report')

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

        worksheet.write_merge(0, 1, 4, 8, 'Employee Entries Report', bold_style_large)
        worksheet.write_merge(3, 3, 1, 3, f'From: {from_date}', bold_style_small)
        worksheet.write_merge(3, 3, 13, 15, f'To: {to_date}', bold_style_small)
        worksheet.write(6, 0, 'No.', bold_style_small)
        worksheet.write_merge(6, 6, 1, 4, 'Employee', bold_style_small)
        worksheet.write_merge(6, 6, 5, 7, 'Vessel', bold_style_small)
        worksheet.write(6, 8, 'Duration', bold_style_small)
        worksheet.write_merge(6, 6, 9, 10, 'Travelling Days', bold_style_small)
        worksheet.write(6, 11, 'Absent Days', bold_style_small)
        worksheet.write(6, 12, 'Bonus', bold_style_small)
        worksheet.write_merge(6, 6, 13, 14, 'Discharge Amount', bold_style_small)
        worksheet.write(6, 15, 'Overtime', bold_style_small)
        worksheet.write_merge(6, 6, 16, 17, 'Shop Deduction', bold_style_small)

        for row, entry in enumerate(entry_list, start=7):
            worksheet.write(row, 0, row - 6)
            worksheet.write_merge(row, row, 1, 4, entry.get('employee', ''))
            worksheet.write_merge(row, row, 5, 7, entry['vessel'])
            worksheet.write(row, 8, entry.get('duration', ''))
            worksheet.write_merge(row, row, 9, 10, entry['travelling_days'])
            worksheet.write(row, 11, entry['absent_days'])
            worksheet.write(row, 12, entry['bonus'])
            worksheet.write_merge(row, row, 13, 14, entry.get('discharge', ''))
            worksheet.write(row, 15, entry['ot'])
            worksheet.write_merge(row, row, 16, 17, entry['shop_deduction'])

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