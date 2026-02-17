# -*- coding: utf-8 -*-
from datetime import datetime
from base64 import encodebytes
from datetime import datetime
from io import BytesIO
import re
from odoo import models, fields, api, _

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class CSHQWizard(models.TransientModel):
    """Monthly Report wizard."""

    _name = "cs.hq.wizard"
    _description = "CS HQ Wizard"

    date_start = fields.Date()
    date_end = fields.Date(required=True, default=fields.Date.context_today)
    fileout = fields.Binary('File', readonly=True)
    fileout_filename = fields.Char('Filename', readonly=True)


    def _get_report_values(self):
        domain = []
        if self.date_start:
            domain.append(('create_date', '>=', self.date_start))
        if self.date_end:
            domain.append(('create_date', '<=', self.date_end))
        tickets = self.env['helpdesk.ticket'].sudo().search(domain, order='ticket_ref ASC')
        return tickets


    def xlsx_print(self):
        active_ids_tmp = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')
        data = {

            'form': self.read()[0],
            'ids': active_ids_tmp,
            'context': {'active_model': active_model},
        }

        file_io = BytesIO()
        workbook = xlsxwriter.Workbook(file_io)
        self.generate_xlsx_report(workbook, data=data)
        workbook.close()
        fout = encodebytes(file_io.getvalue())

        datetime_string = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_name = 'CS HQ Report'
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

    def generate_xlsx_report(self, workbook, data=None, objs=None):

        worksheet = workbook.add_worksheet('CS HQ Report')

        header_format = workbook.add_format(
            {'bold': True, 'border': 1, 'align': 'left', 'text_wrap': True, 'valign': 'vcenter', 'font_size': 10, })
        data_format = workbook.add_format({'border': 1,'align': 'left', 'valign': 'vcenter', 'font_size': 10, })
        long_data_format = workbook.add_format({ 'text_wrap': True,'border': 1,'align': 'left', 'valign': 'vcenter', 'font_size': 10, })
        title_format = workbook.add_format({'bold': True,'border': 1, 'font_size': 16, 'align': 'center', 'valign': 'vcenter'})
        date_range_format = workbook.add_format({'bold': True,'border': 1,'font_size': 12, 'align': 'left', 'valign': 'vcenter'})

        worksheet.merge_range('A1:H1', 'CS HQ Report', title_format)

        if self.date_start:
            date_range_str = f'Date from: {self.date_start.strftime("%d-%m-%Y")} to: {self.date_end.strftime("%d-%m-%Y")}'
        else:
            date_range_str = f'Date Till: {self.date_end.strftime("%d-%m-%Y")}'

        worksheet.merge_range('A2:H2', date_range_str, date_range_format)

        headers = ['Ticket ID', 'Created Date', 'Closed Date', 'Stage', 'Topic', 'Category', 'Mobile No',
                   'Country', 'City', 'Subject', 'Description', 'Customer', 'Phone No', 'Customer Email',
                   'Assigned To', 'Priority', 'Language', 'Messages/Parent Message', 'Messages/Author',
                   'Messages/Created By', 'Messages/Date', 'Messages/Content']


        column_widths = [10, 15, 15, 15, 20, 10, 20, 20, 15, 25, 40, 20, 15, 25, 15, 15, 15, 15, 15, 15, 15, 45]
        for col, width in enumerate(column_widths):
            worksheet.set_column(col, col, width)

        worksheet.write_row('A3', headers, header_format)
        worksheet.set_row(0, 35)
        worksheet.set_row(1, 20)
        worksheet.set_row(2, 25)



        def remove_html_tags(text):
            if text:
                clean_text = re.sub(r'<.*?>', '', text)
                clean_text = re.sub(r'\s+', ' ', clean_text).strip()
                return clean_text
            return ''

        row = 3
        ticket_values = self._get_report_values()
        for vals in ticket_values:
            sorted_messages = sorted(vals.message_ids, key=lambda m: m.date or datetime.min)
            for msg in sorted_messages:
                # if msg.body:
                worksheet.write(row, 0, vals.ticket_ref or '', data_format)
                if vals.create_date:
                    formatted_date = vals.create_date.strftime('%d-%m-%Y %H:%M:%S')
                else:
                    formatted_date = ''
                worksheet.write(row, 1, formatted_date, data_format)
                if vals.close_date:
                    formatted_date_close = vals.close_date.strftime('%d-%m-%Y %H:%M:%S')
                else:
                    formatted_date_close = ''
                worksheet.write(row, 2, formatted_date_close, data_format)
                worksheet.write(row, 3, vals.stage_id.name or '', data_format)
                worksheet.write(row, 4, vals.topic.name or '', data_format)
                worksheet.write(row, 5, vals.category_id.name or '', data_format)
                worksheet.write(row, 6, vals.mob or '', data_format)
                worksheet.write(row, 7, vals.country.name or '', data_format)
                worksheet.write(row, 8, vals.city_text or '', data_format)
                worksheet.write(row, 9, vals.subject or '', data_format)
                clean_description = remove_html_tags(vals.description or '')
                worksheet.write(row, 10, clean_description, data_format)
                worksheet.write(row, 11, vals.partner_id.name or '', data_format)
                worksheet.write(row, 12, vals.partner_phone or '', data_format)
                worksheet.write(row, 13, vals.partner_email or '', data_format)
                worksheet.write(row, 14, vals.user_id.name or '', data_format)
                priority = dict(vals._fields['priority'].selection).get(vals.priority, '')
                worksheet.write(row, 15, priority or '', data_format)
                language = dict(vals._fields['kg_pre_lang'].selection).get(vals.kg_pre_lang, '')
                worksheet.write(row, 16, language or '', data_format)
                worksheet.write(row, 17, msg.parent_id.display_name or '', data_format)
                # worksheet.write(row, 17, msg.parent_id.record_name or '', data_format)
                worksheet.write(row, 18, msg.author_id.name or '', data_format)
                worksheet.write(row, 19, msg.create_uid.name or '', data_format)
                if msg.date:
                    format_date = msg.date.strftime('%d-%m-%Y %H:%M:%S')
                else:
                    format_date = ''
                worksheet.write(row, 20, format_date, data_format)
                clean_body = remove_html_tags(msg.body or '')
                worksheet.write(row, 21, clean_body, long_data_format)
                row += 1
