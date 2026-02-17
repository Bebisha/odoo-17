# -*- coding: utf-8 -*-

import base64
from io import BytesIO

import xlwt

from odoo import models, fields
from odoo.exceptions import ValidationError


class FuelUsageAnalysisReport(models.TransientModel):
    _name = 'fuel.usage.analysis.report.wizard'
    _description = 'fuel.usage.analysis.report.wizard'

    date_from = fields.Date(string='From')
    date_to = fields.Date(string='To')
    vessel_id = fields.Many2one('sponsor.sponsor', string='Vessel', required=True)

    def get_data(self):
        """ Function to get data for the report """
        for fuel in self:
            fuel_list = []
            fuel_usage_analysis = self.env['fuel.usage.analysis'].search(
                [('date', '>=', fuel.date_from), ('date', '<=', fuel.date_to),
                 ('vessel_id', '=', fuel.vessel_id.id)])
            if fuel_usage_analysis:
                for fuel_analysis in fuel_usage_analysis:
                    fuel_data = {
                        'activity': fuel_analysis.activity_id.name,
                        'date': fields.Date.to_date(fuel_analysis.date).strftime('%d-%m-%Y'),
                        'tons_mgo': fuel_analysis.tons_mgo,
                        'tons_hfo': fuel_analysis.tons_hfo,
                    }
                    fuel_list.append(fuel_data)
            return fuel_list

    def get_total_data(self):
        """ Function to get total data for the report """
        for fuel in self:
            fuel_total_dict = {}
            fuel_usage_analysis = self.env['fuel.usage.analysis'].search(
                [('date', '>=', fuel.date_from), ('date', '<=', fuel.date_to),
                 ('vessel_id', '=', fuel.vessel_id.id)]
            )

            if fuel_usage_analysis:
                for fuel_analysis in fuel_usage_analysis:
                    activity = fuel_analysis.activity_id.name
                    date_str = fields.Date.to_date(fuel_analysis.date).strftime('%Y-%m-%d')

                    if activity not in fuel_total_dict:
                        fuel_total_dict[activity] = {
                            'activity': activity,
                            'total_tons_mgo': 0.0,
                            'total_tons_hfo': 0.0,
                            'days_set': set()
                        }

                    fuel_total_dict[activity]['total_tons_mgo'] += fuel_analysis.tons_mgo
                    fuel_total_dict[activity]['total_tons_hfo'] += fuel_analysis.tons_hfo

                    fuel_total_dict[activity]['days_set'].add(date_str)

            fuel_total_list = []
            for data in fuel_total_dict.values():
                data['days'] = len(data.pop('days_set'))
                fuel_total_list.append(data)

            return fuel_total_list

    def action_print_xlsx(self):
        """ Acton to print excel report """
        fuel_list = self.get_data()
        if not fuel_list:
            raise ValidationError("There is no data in the selected time period!")
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Fuel Usage Analysis Report')

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

        worksheet.write_merge(0, 1, 4, 9, 'Fuel Usage Analysis Report', bold_style_large)
        worksheet.write_merge(3, 4, 4, 9, self.vessel_id.name, bold_style_large)
        worksheet.write_merge(5, 5, 4, 9, from_date, bold_style_small)

        worksheet.write(9, 0, 'Date', bold_style_small)
        worksheet.write_merge(9, 9, 1, 3, 'Activity', bold_style_small)

        worksheet.write_merge(7, 7, 4, 7, 'Daily use of fuel', bold_style_small)
        worksheet.write_merge(8, 8, 4, 7, 'Tons', bold_style_small)

        worksheet.write_merge(9, 9, 4, 5, 'MGO', bold_style_small)
        worksheet.write_merge(9, 9, 6, 7, 'HFO', bold_style_small)

        for row, fuel in enumerate(fuel_list, start=10):
            worksheet.write(row, 0, fuel['date'])
            worksheet.write_merge(row, row, 1, 3, fuel['activity'])
            worksheet.write_merge(row, row, 4, 5, fuel['tons_mgo'])
            worksheet.write_merge(row, row, 6, 7, fuel['tons_hfo'])

        fuel_total_list = self.get_total_data()

        total_head_row = row + 3
        worksheet.write_merge(total_head_row, total_head_row, 0, 3, 'Activity', bold_style_small)
        worksheet.write_merge(total_head_row, total_head_row, 4, 5, 'MGO', bold_style_small)
        worksheet.write_merge(total_head_row, total_head_row, 6, 7, 'HFO', bold_style_small)
        worksheet.write_merge(total_head_row, total_head_row, 8, 9, 'Days', bold_style_small)

        for total_row, data in enumerate(fuel_total_list, start=total_head_row+1):
            worksheet.write_merge(total_row, total_row, 0, 3, data['activity'])
            worksheet.write_merge(total_row, total_row, 4, 5, data['total_tons_mgo'])
            worksheet.write_merge(total_row, total_row, 6, 7, data['total_tons_hfo'])
            worksheet.write_merge(total_row, total_row, 8, 9, data['days'])

        output = BytesIO()
        workbook.save(output)
        output.seek(0)
        attachment = self.env['ir.attachment'].create({
            'name': 'Fuel_Usage_Analysis_Report.xls',
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
