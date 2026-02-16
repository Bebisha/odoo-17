from odoo import fields, models, api, _
from base64 import encodebytes
from datetime import datetime, timedelta
from io import BytesIO
from odoo.exceptions import ValidationError, UserError

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class OTReportWizard(models.TransientModel):
    _name = "ot.report.wizard"
    _description = "OT Report"

    date_from = fields.Datetime('From', default=fields.Date.today())
    date_to = fields.Datetime('To', default=fields.Date.today())
    fileout = fields.Binary('File', readonly=True)
    fileout_filename = fields.Char('Filename', readonly=True)

    def print_sif_xlsx(self):
        ot_list = []
        emp_list = []
        if self.date_from > self.date_to:
            raise ValidationError(_('Start Date must be less than End Date'))
        # if self.date_from and self.date_to:
        #     if self.date_from.month != self.date_to.month:
        #         raise UserError(_('OT Report can only be printed for the same month!'))
        active_ids_tmp = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')

        overtime_list = self.env['hr.overtime'].search([
            ('type', '=', 'cash'),
            ('date_from', '>', self.date_from),
            ('date_to', '>', self.date_from),
            ('date_from', '<', self.date_to),
            ('date_to', '<', self.date_to),
        ])
        for ot in overtime_list:
            if ot.employee_id not in emp_list:
                emp_list.append(ot.employee_id)
        ot_tot = 0.0
        bs_tot = 0.0
        day_tot = 0.0
        night_tot = 0.0
        ph_tot = 0.0
        for emp in emp_list:
            hrs_day = 0.0
            hrs_night = 0.0
            hrs_ph = 0.0
            rate_day = 0.0
            rate_night = 0.0
            rate_ph = 0.0
            total = 0.0
            for ot in overtime_list:
                if emp.name == ot.employee_id.name:
                    if ot.shift_type == 'day':
                        hrs_day += ot.days_no_tmp
                        rate_day += ot.overtime_amount
                    elif ot.shift_type == 'night':
                        hrs_night += ot.days_no_tmp
                        rate_night += ot.overtime_amount
                    elif ot.shift_type == 'restday_public_holiday':
                        hrs_ph += ot.days_no_tmp
                        rate_ph += ot.overtime_amount
                    total = rate_ph + rate_night + rate_day
            day_tot += rate_day
            night_tot += rate_night
            ph_tot += rate_ph
            bs_tot += emp.contract_id.total_salary
            ot_tot += total
            lis = {
                'emp_name': emp.name,
                'emp_no': emp.registration_number,
                'dept': emp.department_id.name,
                'cost_center': emp.contract_id.analytic_account_id.name,
                'basic_sal': emp.contract_id.total_salary,
                'basic_per_hr': emp.contract_id.over_hour,
                'hrs_day': hrs_day,
                'hrs_night': hrs_night,
                'hrs_ph': hrs_ph,
                'rate_day': rate_day,
                'rate_night': rate_night,
                'rate_ph': rate_ph,
                'total': total,
            }
            ot_list.append(lis)

        data = {
            'form': self.read()[0],
            'ot_list': ot_list,
            'ot_tot': ot_tot,
            'bs_tot': bs_tot,
            'day_tot': day_tot,
            'night_tot': night_tot,
            'ph_tot': ph_tot,
            'ids': active_ids_tmp,
            'context': {'active_model': active_model},
        }
        file_io = BytesIO()
        workbook = xlsxwriter.Workbook(file_io)

        self.get_xlsx_report(workbook, data)
        workbook.close()
        fout = encodebytes(file_io.getvalue())
        datetime_string = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_name = 'OT Report'
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

    def get_xlsx_report(self, workbook, data):
        ot_list = data['ot_list']
        ot_tot = data['ot_tot']
        bs_tot = data['bs_tot']
        day_tot = data['day_tot']
        night_tot = data['night_tot']
        ph_tot = data['ph_tot']
        sheet = workbook.add_worksheet()
        cell_format = workbook.add_format({'font_size': '11px', 'align': 'center', 'valign': 'vcenter', 'border': 1,
                                           'top': 2})
        # cell_format4 = workbook.add_format({'font_size': '11px', 'align': 'center', 'valign': 'vcenter', 'border': 1,
        #                                    'top': 2, 'bg_color': '#FFFF99'})
        cell_format2 = workbook.add_format({'font_size': '11px', 'align': 'center', 'valign': 'vcenter', 'border': 2})
        cell_format3 = workbook.add_format({'font_size': '11px', 'align': 'center', 'valign': 'vcenter', 'border': 1, 'right': 2})
        cell_format1 = workbook.add_format(
            {'font_size': '12px', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'border': 1,
             'top': 2})
        head = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '13px'})
        txt = workbook.add_format({'font_size': '10px', 'align': 'center', 'border': 1})
        txt4 = workbook.add_format({'font_size': '10px', 'align': 'center', 'border': 1, 'bg_color': '#FFFF99'})
        txt2 = workbook.add_format({'font_size': '10px', 'align': 'right', 'border': 1, 'bottom': 2,
                                    'num_format': '0.000'})
        txt3 = workbook.add_format({'font_size': '10px', 'align': 'right', 'border': 1, 'bottom': 2, 'right': 2,
                                    'num_format': '0.000'})
        txt1 = workbook.add_format({'font_size': '10px', 'align': 'center'})
        amt = workbook.add_format({'font_size': '10px', 'align': 'right', 'num_format': '0.000', 'border': 1})
        amt1 = workbook.add_format({'font_size': '10px', 'align': 'right', 'num_format': '0.000', 'border': 1,
                                    'right': 2})
        bold = workbook.add_format({'bold': True, 'font_size': '10px', 'align': 'center'})
        bold1 = workbook.add_format({'bold': True, 'font_size': '10px', 'align': 'center', 'border': 1, 'bottom': 2})

        sheet.set_row(3, 20)
        sheet.set_row(4, 50)
        sheet.set_column(0, 0, 20)
        sheet.set_column(1, 1, 15)
        sheet.set_column(2, 2, 10)
        sheet.set_column(3, 3, 30)
        sheet.set_column(4, 4, 15)
        sheet.set_column(5, 5, 10)
        sheet.set_column(6, 6, 10)
        sheet.set_column(7, 7, 10)
        sheet.set_column(8, 8, 10)
        sheet.set_column(9, 9, 10)
        sheet.set_column(10, 10, 10)
        sheet.set_column(11, 11, 10)
        sheet.set_column(12, 12, 10)

        month = self.date_from.strftime('%B %Y')
        sheet.merge_range('A1:M1', 'MASIRAH OIL LIMITED', head)
        sheet.merge_range('A2:M2', 'Local Staff Overtime Statement', cell_format)
        sheet.merge_range('A3:M3', f'For the period of {month}', cell_format2)

        sheet.merge_range('G4:I4', 'Number Of Hours', cell_format2)
        sheet.merge_range('J4:M4', 'OT Amount', cell_format2)

        sheet.write('A5', 'Dept', cell_format)
        sheet.write('B5', 'Cost Center', cell_format)
        sheet.write('C5', 'Emp. No.', cell_format)
        sheet.write('D5', 'Staff Name.', cell_format)
        sheet.write('E5', 'Official Total Salary', cell_format1)
        sheet.write('F5', 'Basic Hours Rate', cell_format1)
        sheet.write('G5', 'Day', cell_format)
        sheet.write('H5', 'Night', cell_format)
        sheet.write('I5', 'Public Holidays', cell_format1)
        sheet.write('J5', '1.25 Times', cell_format)
        sheet.write('K5', '1.5 Times', cell_format)
        sheet.write('L5', '2 Times', cell_format)
        sheet.write('M5', 'Total', cell_format3)

        row = 6
        for rec in ot_list:
            sheet.write('A' + str(row), rec['dept'] or '', txt)
            sheet.write('B' + str(row), rec['cost_center'] or '', txt)
            sheet.write('C' + str(row), rec['emp_no'] or '', txt4)
            sheet.write('D' + str(row), rec['emp_name'] or '', txt)
            sheet.write('E' + str(row), rec['basic_sal'] or '', amt)
            sheet.write('F' + str(row), rec['basic_per_hr'] or '', amt)
            sheet.write('G' + str(row), rec['hrs_day'] or '', txt4)
            sheet.write('H' + str(row), rec['hrs_night'] or '', txt4)
            sheet.write('I' + str(row), rec['hrs_ph'] or '', txt4)
            sheet.write('J' + str(row), rec['rate_day'] or '', amt)
            sheet.write('K' + str(row), rec['rate_night'] or '', amt)
            sheet.write('L' + str(row), rec['rate_ph'] or '', amt)
            sheet.write('M' + str(row), rec['total'] or '', amt1)
            row += 1

        sheet.write('A' + str(row), '', amt)
        sheet.write('B' + str(row), '', amt)
        sheet.write('C' + str(row), '', amt)
        sheet.write('D' + str(row), '', amt)
        sheet.write('E' + str(row), '', amt)
        sheet.write('F' + str(row), '', amt)
        sheet.write('G' + str(row), '', amt)
        sheet.write('H' + str(row), '', amt)
        sheet.write('I' + str(row), '', amt)
        sheet.write('J' + str(row), '', amt)
        sheet.write('K' + str(row), '', amt)
        sheet.write('L' + str(row), '', amt)
        sheet.write('M' + str(row), '', amt1)

        sheet.write('A' + str(row + 1), 'Total', bold1)
        sheet.write('B' + str(row + 1), '', txt2)
        sheet.write('C' + str(row + 1), '', txt2)
        sheet.write('D' + str(row + 1), '', txt2)
        sheet.write('E' + str(row + 1), bs_tot or '', txt2)
        sheet.write('F' + str(row + 1), '', txt2)
        sheet.write('G' + str(row + 1), '', txt2)
        sheet.write('H' + str(row + 1), '', txt2)
        sheet.write('I' + str(row + 1), '', txt2)
        sheet.write('J' + str(row + 1), day_tot or '', txt2)
        sheet.write('K' + str(row + 1), night_tot or '', txt2)
        sheet.write('L' + str(row + 1), ph_tot or '', txt2)
        sheet.write('M' + str(row + 1), ot_tot or '', txt3)

        # sheet.write('A' + str(row + 2), '', amt)
        # sheet.write('B' + str(row + 2), '', amt)
        # sheet.write('C' + str(row + 2), '', amt)
        # sheet.write('D' + str(row + 2), '', amt)
        # sheet.write('E' + str(row + 2), '', amt)
        # sheet.write('F' + str(row + 2), '', amt)
        # sheet.write('G' + str(row + 2), '', amt)
        # sheet.write('H' + str(row + 2), '', amt)
        # sheet.write('I' + str(row + 2), '', amt)
        # sheet.write('J' + str(row + 2), '', amt)
        # sheet.write('K' + str(row + 2), '', amt)
        # sheet.write('L' + str(row + 2), '', amt)
        # sheet.write('M' + str(row + 2), '', amt)

        sheet.write('A' + str(row + 5), 'Prepared By:', bold)
        sheet.write('A' + str(row + 8), 'Date:', txt1)
        sheet.write('E' + str(row + 5), 'Checking By:', bold)
        sheet.write('E' + str(row + 8), 'Date:', txt1)
