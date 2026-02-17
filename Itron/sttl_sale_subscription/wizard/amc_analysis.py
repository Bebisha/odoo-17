import xlsxwriter

from odoo import api, models, fields
from datetime import date
from odoo.exceptions import ValidationError

import xlwt
import base64
from io import BytesIO


class AMCAnalysis(models.TransientModel):
    _name = 'amc.analysis'
    _rec_name = 'project_id'

    project_id = fields.Many2one('project.project', string="Project")
    contract_id = fields.Many2one('project.contract.request.amc', string="Contract")
    start_date = fields.Date(string='Start Date', store=True)
    end_date = fields.Date(string='End Date', store=True)

    @api.onchange('project_id')
    def _onchange_project_id(self):
        """ Fetching Latest Contract """
        self.contract_id = False
        self.start_date = False
        self.end_date = False
        if self.project_id:
            contract = self.env['project.contract.request.amc'].search([
                ('project_id', '=', self.project_id.id),
                ('rebion_status', '=', 'done')
            ], limit=1)
            if contract:
                self.write({
                    'contract_id': contract,
                    'start_date': contract.date_start,
                    'end_date': contract.date_end,
                })

    @api.onchange('contract_id')
    def onchange_contract_id(self):
        """ Start and End Date based on Contract """
        self.write({
            'start_date': self.contract_id.date_start,
            'end_date': self.contract_id.date_end,
        })

    def get_data(self):
        """ Get data for report """
        tasks = self.env['project.task'].sudo().search([
            ('project_id', '=', self.project_id.id),
            ('date_start', '>=', self.start_date),
            ('date_deadline', '<=', self.end_date),
        ])

        all_data = []
        selection_dict = dict(self.env['project.task']._fields['task_type'].selection)

        for task in tasks:
            task_type_value = task.task_type
            task_type_label = selection_dict.get(task_type_value, 'Undefined')

            task_hours = task.allocated_hours or 0.0
            hours = int(task_hours)
            minutes = int(round((task_hours - hours) * 60))
            time_formatted = f"{hours}h {minutes}m" if task_hours else "0h 0m"

            task_info = {
                'task_name': task.name,
                'task_type_value': task_type_value,
                'task_type_label': task_type_label,
                'ticket': task.ticket_id.number if task.ticket_id else 'NIL',
                'start_date': task.date_start or '',
                'deadline': task.date_deadline or '',
                'spent_hrs': time_formatted,
                'spent_hrs_raw': task_hours,
                'stage': task.stage_id.name or '',
            }
            all_data.append(task_info)

        return all_data

    def action_print_xlsx(self):
        """ Action to print AMC xlsx report using xlsxwriter """
        data = self.get_data()
        if not data:
            raise ValidationError("There is no data in the selected time period")

        from_date = fields.Date.to_date(self.start_date).strftime('%d %B %Y')
        to_date = fields.Date.to_date(self.end_date).strftime('%d %B %Y')

        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet("AMC Report")

        # === Styles ===
        bold = workbook.add_format({'bold': True, 'font_size': 12})
        bold_center_grey = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter',
                                                'bg_color': '#D9D9D9', 'border': 1})
        bold_border = workbook.add_format({'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter'})
        border = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter'})
        wrap_border = workbook.add_format({'text_wrap': True, 'valign': 'vcenter', 'align': 'left', 'border': 1})
        date_format = workbook.add_format(
            {'num_format': 'dd/mm/yyyy', 'border': 1, 'align': 'center', 'valign': 'vcenter'})

        # Column widths
        for col in range(12):
            worksheet.set_column(col, col, 12)

        row = 0

        # === Title ===
        worksheet.merge_range(row, 0, row, 11, f'AMC Report for {self.project_id.name}', bold_center_grey)
        worksheet.set_row(row, 25)
        row += 2

        # === From/To ===
        worksheet.merge_range(row, 0, row, 3, f'From: {from_date}', bold)
        worksheet.merge_range(row, 4, row, 6, f'To: {to_date}', bold)
        worksheet.set_row(row, 25)
        row += 2

        # === Planned Hours ===
        worksheet.merge_range(row, 0, row, 1, "Planned Hours", bold)
        worksheet.write(row, 2, self.contract_id.planned_hrs, bold)
        worksheet.set_row(row, 25)
        row += 2

        # === Table Header ===
        worksheet.write(row, 0, 'Ticket No.', bold_center_grey)
        worksheet.merge_range(row, 1, row, 5, 'Task', bold_center_grey)
        worksheet.merge_range(row, 6, row, 7, 'Task Type', bold_center_grey)
        worksheet.write(row, 8, 'Start Date', bold_center_grey)
        worksheet.write(row, 9, 'End Date', bold_center_grey)
        worksheet.write(row, 10, 'Spent Hours', bold_center_grey)
        worksheet.write(row, 11, 'Stage', bold_center_grey)
        worksheet.set_row(row, 25)
        row += 1
        total_spent_hours = 0
        task_type_map = {}

        task_type_map = {}

        for task in data:
            type_key = task.get('task_type_value') or 'undefined'
            spent_hrs_raw = task.get('spent_hrs_raw') or 0.0
            task_type_map.setdefault(type_key, {'label': task.get('task_type_label'), 'total': 0.0})
            task_type_map[type_key]['total'] += spent_hrs_raw

            # Write each row
            worksheet.write(row, 0, task.get('ticket'), border)
            worksheet.merge_range(row, 1, row, 5, task.get('task_name', ''), wrap_border)
            worksheet.merge_range(row, 6, row, 7, task.get('task_type_label', ''), border)
            worksheet.write(row, 8, task.get('start_date') or '',
                            date_format if task.get('start_date') else border)
            worksheet.write(row, 9, task.get('deadline') or '',
                            date_format if task.get('deadline') else border)
            worksheet.write(row, 10, task.get('spent_hrs') or 0, border)
            worksheet.write(row, 11, task.get('stage', ''), border)
            total_spent_hours += spent_hrs_raw
            worksheet.set_row(row, 40)
            row += 1

        # === Task Type Wise Totals ===
        row += 1
        worksheet.merge_range(row, 8, row, 10, "Summary", bold_center_grey)
        row += 1
        worksheet.merge_range(row, 8, row, 9, "Task Type", bold_center_grey)
        worksheet.write(row, 10, "Total Hours", bold_center_grey)
        row += 1
        for type_key, val in task_type_map.items():
            total = val['total']
            h = int(total)
            m = int(round((total - h) * 60))
            formatted = f"{h}h {m}m"
            worksheet.merge_range(row, 8, row, 9, val['label'], border)
            worksheet.write(row, 10, formatted, border)
            row += 1

        # === Total Spent Hours Row ===
        # row += 1
        total_hours = int(total_spent_hours)
        total_minutes = int(round((total_spent_hours - total_hours) * 60))
        total_time_formatted = f"{total_hours}h {total_minutes}m"
        # worksheet.write(row, 0, "", border)
        # worksheet.merge_range(row, 1, row, 5, "", border)
        # worksheet.merge_range(row, 6, row, 7, "", border)
        worksheet.merge_range(row, 8, row, 9, "Total Spent Hours", bold_border)
        worksheet.write(row, 10, total_time_formatted, bold_border)
        # worksheet.write(row, 11, "", border)
        worksheet.set_row(row, 25)

        workbook.close()
        output.seek(0)
        attachment = self.env['ir.attachment'].create({
            'name': 'AMC_Report.xlsx',
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
