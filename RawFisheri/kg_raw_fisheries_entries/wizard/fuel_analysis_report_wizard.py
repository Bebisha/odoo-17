# -*- coding: utf-8 -*-

import base64
from io import BytesIO

import xlwt

from odoo import models, fields
from odoo.exceptions import ValidationError


class FuelAnalysisReport(models.TransientModel):
    _name = 'fuel.analysis.report.wizard'
    _description = 'fuel.analysis.report.wizard'

    date_from = fields.Date(string='From')
    date_to = fields.Date(string='To')
    vessel_id = fields.Many2one('sponsor.sponsor', string='Vessel', required=True)

    def get_data(self):
        """ Function to get data for the report """
        for fuel in self:
            fuel_list = []
            fuel_analyses = self.env['fuel.analysis'].search(
                [('date', '>=', fuel.date_from), ('date', '<=', fuel.date_to),
                 ('vessel_id', '=', fuel.vessel_id.id)])
            if fuel_analyses:
                for fuel_analysis in fuel_analyses:
                    fuel_data = {
                        'name': fuel_analysis.name,
                        'tons_mgo': fuel_analysis.tons_mgo,
                        'tons_hfo': fuel_analysis.tons_hfo,
                        'usd_mgo': fuel_analysis.usd_mgo,
                        'usd_hfo': fuel_analysis.usd_hfo,
                        'price_avg_mgo': fuel_analysis.price_avg_mgo,
                        'price_avg_hfo': fuel_analysis.price_avg_hfo,
                    }
                    fuel_list.append(fuel_data)
            return fuel_list

    def action_print_xlsx(self):
        """ Acton to print excel report """
        fuel_list = self.get_data()
        if not fuel_list:
            raise ValidationError("There is no data in the selected time period!")
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Fuel Cost Analysis Report')

        from_date = fields.Date.to_date(self.date_from).strftime('%B %Y')
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

        worksheet.write_merge(0, 1, 4, 9, 'Fuel Cost Analysis Report', bold_style_large)
        worksheet.write_merge(3, 4, 4, 9, self.vessel_id.name, bold_style_large)
        worksheet.write_merge(5, 5, 4, 9, from_date, bold_style_small)

        worksheet.write_merge(7, 7, 4, 5, 'Tons', bold_style_small)
        worksheet.write_merge(7, 7, 6, 7, 'USD', bold_style_small)
        worksheet.write_merge(7, 7, 8, 9, 'Price(Average)', bold_style_small)

        worksheet.write(8, 4, 'MGO', bold_style_small)
        worksheet.write(8, 5, 'HFO', bold_style_small)
        worksheet.write(8, 6, 'MGO', bold_style_small)
        worksheet.write(8, 7, 'HFO', bold_style_small)
        worksheet.write(8, 8, 'MGO', bold_style_small)
        worksheet.write(8, 9, 'HFO', bold_style_small)

        for row, fuel in enumerate(fuel_list, start=9):
            worksheet.write_merge(row, row, 0, 3, fuel['name'])
            worksheet.write(row, 4, fuel['tons_mgo'])
            worksheet.write(row, 5, fuel['tons_hfo'])
            worksheet.write(row, 6, fuel['usd_mgo'])
            worksheet.write(row, 7, fuel['usd_hfo'])
            worksheet.write(row, 8, round(fuel['price_avg_mgo'], 2))
            worksheet.write(row, 9, round(fuel['price_avg_hfo'], 2))

        total_tons_mgo = sum(fuel['tons_mgo'] for fuel in fuel_list)
        total_tons_hfo = sum(fuel['tons_hfo'] for fuel in fuel_list)
        total_usd_mgo = sum(fuel['usd_mgo'] for fuel in fuel_list)
        total_usd_hfo = sum(fuel['usd_hfo'] for fuel in fuel_list)
        total_usd_avg_mgo = sum(fuel['price_avg_mgo'] for fuel in fuel_list)
        total_usd_avg_hfo = sum(fuel['price_avg_hfo'] for fuel in fuel_list)

        total_row = row + 1
        worksheet.write_merge(total_row, total_row, 0, 3, 'Total purchase in the month', bold_style_small)
        worksheet.write(total_row, 4, total_tons_mgo, right_align_style)
        worksheet.write(total_row, 5, total_tons_hfo, right_align_style)
        worksheet.write(total_row, 6, total_usd_mgo, right_align_style)
        worksheet.write(total_row, 7, total_usd_hfo, right_align_style)
        worksheet.write(total_row, 8, total_usd_avg_mgo, right_align_style)
        worksheet.write(total_row, 9, total_usd_avg_hfo, right_align_style)

        output = BytesIO()
        workbook.save(output)
        output.seek(0)
        attachment = self.env['ir.attachment'].create({
            'name': 'Fuel_Cost_Analysis_Report.xls',
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
