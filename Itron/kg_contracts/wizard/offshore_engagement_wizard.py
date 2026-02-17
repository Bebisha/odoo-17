from collections import OrderedDict

from odoo import fields, models, api, _
from base64 import encodebytes
from datetime import datetime, timedelta, date
from io import BytesIO
from odoo.exceptions import ValidationError, UserError

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class KGOffshoreEngagementWizard(models.TransientModel):
    """offshore engagement report wizard."""

    _name = 'project.offshore.engagement.wizard'
    _description = 'Report Wizard'

    date_from = fields.Date()
    date_to = fields.Date()
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  default=lambda self: self.env.company.currency_id.id)
    company_id = fields.Many2one(comodel_name='res.company', default=lambda self: self.env.user.company_id,
                                 string='Company')

    fileout = fields.Binary('File', readonly=True)
    fileout_filename = fields.Char('Filename', readonly=True)

    def print_excel(self):

        if self.date_from > self.date_to:
            raise ValidationError(_('Start Date must be less than End Date'))

        if self.date_from and self.date_to:
            if self.date_from.month != self.date_to.month:
                raise UserError(_('The Payslip of the same month will be printed'))

        """ button action to print xlsx report of offshore engagement"""

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
        report_name = 'Offshore Engagement Report'
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
        contracts = self.env['project.contract.request'].search(
            [('contract_type', '=', 'offshore'), ('state', '=', 'approve')])

        header_row_style = workbook.add_format({'bold': True, 'align': 'center', 'border': True})

        sheet = workbook.add_worksheet()
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '15px', 'bg_color': 'yellow'})
        total = workbook.add_format(
            {'align': 'center', 'bold': True, 'bg_color': 'orange'})

        txt = workbook.add_format({'font_size': '10px', 'align': 'left'})

        date_style = workbook.add_format(
            {'text_wrap': True, 'font_size': '10px', 'num_format': 'dd-mm-yyyy', 'align': 'center'})

        amt = workbook.add_format({'font_size': '10px', 'align': 'right'})
        sl_no = workbook.add_format({'font_size': '10px', 'align': 'center'})

        bold = workbook.add_format({'bold': True, 'font_size': '12px', 'align': 'center'})
        bold_total = workbook.add_format({'bold': True, 'font_size': '10px', 'align': 'center'})
        bold_total_amount = workbook.add_format({'bold': True, 'font_size': '10px', 'align': 'right'})

        row = 0
        col = 2

        sheet.merge_range('A1:D2', 'Summary Report-Resource Engagement', head)
        sheet.set_column('A1:D2', 30)
        sheet.write('A3', 'Project', header_row_style)
        sheet.write('A4', 'Resource Engagement model', header_row_style)
        sheet.write('A5', 'Start Date', header_row_style)
        sheet.write('A6', 'End Date', header_row_style)
        sheet.write('A7', 'Team Lead', header_row_style)
        sheet.write('A8', 'Resource Name', header_row_style)
        sheet.write('A9', 'Open Tasks', header_row_style)
        sheet.write('A10', 'In progress Tasks', header_row_style)
        sheet.write('A11', 'Over Due  Tasks', header_row_style)
        sheet.write('A12', 'Hold Tasks', header_row_style)
        sheet.write('A13', 'Completed Tasks', header_row_style)
        sheet.write('A14', 'Total Tasks', total)
        sheet.write('A15', 'Current Project Status', header_row_style)

        data_start_row = 1

        for rec in contracts:
            names = [user.name for user in rec.project_id.project_team_user_ids]
            tasks_in_progress = [task for task in rec.project_id.task_ids if task.stage_id.is_progress]
            count_tasks_in_progress = len(tasks_in_progress)

            tasks_open = [task for task in rec.project_id.task_ids if task.stage_id.is_open]
            count_tasks_open = len(tasks_open)

            tasks_hold = [task for task in rec.project_id.task_ids if task.stage_id.is_hold]
            count_tasks_hold = len(tasks_hold)

            tasks_completed = [task for task in rec.project_id.task_ids if task.stage_id.is_fixed]
            count_tasks_completed = len(tasks_completed)
            today = date.today()

            tasks_with_past_end_date = [task for task in rec.project_id.task_ids if
                                        task.date_deadline and task.date_deadline < today]
            count_tasks_with_past_end_date = len(tasks_with_past_end_date)

            total_tasks = (
                    count_tasks_in_progress +
                    count_tasks_open +
                    count_tasks_hold +
                    count_tasks_completed +
                    count_tasks_with_past_end_date
            )

            # rr

            # Join the names with a comma
            names_str = ", ".join(names)
            sheet.write(col, data_start_row + row, rec.project_id.name, bold)
            sheet.write(col + 1, data_start_row + row, rec.recurring_id.name, sl_no)
            sheet.write(col + 2, data_start_row + row, rec.date_start, date_style)
            sheet.write(col + 3, data_start_row + row, rec.date_end, date_style)
            sheet.write(col + 4, data_start_row + row, rec.project_id.user_id.name, bold_total)
            sheet.write(col + 5, data_start_row + row, names_str, bold_total)
            sheet.write(col + 6, data_start_row + row, count_tasks_open, sl_no)
            sheet.write(col + 7, data_start_row + row, count_tasks_in_progress, sl_no)
            sheet.write(col + 8, data_start_row + row, count_tasks_with_past_end_date, sl_no)
            sheet.write(col + 9, data_start_row + row, count_tasks_hold, sl_no)
            sheet.write(col + 10, data_start_row + row, count_tasks_completed, sl_no)
            sheet.write(col + 11, data_start_row + row, total_tasks, total)
            sheet.write(col + 12, data_start_row + row, rec.project_id.stage_id.name, sl_no)
            row += 1
