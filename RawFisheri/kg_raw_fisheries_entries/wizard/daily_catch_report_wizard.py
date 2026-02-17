# -*- coding: utf-8 -*-

import base64
from io import BytesIO

import xlwt

from odoo import models, fields
from odoo.exceptions import ValidationError


class DailyCatchReport(models.TransientModel):
    _name = 'daily.catch.report.wizard'
    _description = 'daily.catch.report.wizard'

    date_from = fields.Date(string='From')
    date_to = fields.Date(string='To')
    vessel_id = fields.Many2one('sponsor.sponsor', string='Vessel', required=True)

    def get_data(self):
        """ Function to get data for the report """
        for catch in self:
            catch_list = []
            daily_catches = self.env['daily.catch'].search(
                [('date', '>=', catch.date_from), ('date', '<=', catch.date_to),
                 ('vessel_id', '=', catch.vessel_id.id)])
            if daily_catches:
                total_catch = 0
                count = 0
                for daily_catch in daily_catches:
                    total_catch += daily_catch.catch_of_day
                    count += 1
                    average = total_catch / count
                    catch_data = {
                        'date': fields.Date.to_date(daily_catch.date).strftime('%d-%m-%Y'),
                        'vessel': daily_catch.vessel_id.name,
                        'total_on_board': daily_catch.total_on_board,
                        'catch_of_day': daily_catch.catch_of_day,
                        'average': average,
                    }
                    catch_list.append(catch_data)
            return catch_list

    def action_print_xlsx(self):
        """ Acton to print excel report """
        catch_list = self.get_data()
        if not catch_list:
            raise ValidationError("There is no data in the selected time period!")
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Daily Catch Report')

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

        right_align_style = xlwt.XFStyle()
        right_alignment = xlwt.Alignment()
        right_alignment.horz = xlwt.Alignment.HORZ_RIGHT
        right_align_style.alignment = right_alignment

        row_height = 30
        worksheet.row(6).set_style(xlwt.easyxf(f'font: height {row_height * 20};'))

        worksheet.write_merge(0, 1, 4, 8, 'Daily Catch Report', bold_style_large)
        worksheet.write_merge(3, 3, 1, 3, f'From: {from_date}', bold_style_small)
        worksheet.write_merge(3, 3, 10, 12, f'To: {to_date}', bold_style_small)

        worksheet.write_merge(6, 7, 3, 12, self.vessel_id.name, bold_style_large)
        worksheet.write_merge(8, 8, 0, 2,'Date', bold_style_small)
        worksheet.write_merge(8, 8, 3, 5, 'Total On Board', bold_style_small)
        worksheet.write_merge(8, 8, 6, 9, 'Catch For The Day', bold_style_small)
        worksheet.write_merge(8, 8, 10, 12, 'Average', bold_style_small)

        for row, catch in enumerate(catch_list, start=9):
            worksheet.write_merge(row, row, 0, 2, catch['date'], right_align_style)
            worksheet.write_merge(row, row, 3, 5, catch['total_on_board'])
            worksheet.write_merge(row, row, 6, 9, catch['catch_of_day'])
            worksheet.write_merge(row, row, 10, 12, catch['average'])

        output = BytesIO()
        workbook.save(output)
        output.seek(0)
        attachment = self.env['ir.attachment'].create({
            'name': 'Daily_Catch_Report.xls',
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
