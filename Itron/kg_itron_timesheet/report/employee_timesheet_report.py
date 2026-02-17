# -*- coding: utf-8 -*-
from datetime import datetime
import pytz
from pytz import timezone, UTC

from odoo import api, models, fields



class EmployeeTimesheetReport(models.Model):
    _name = 'employee.timesheet.report'
    _description = 'Employee Timesheet Report'

    name = fields.Char(compute='_compute_name')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    date = fields.Date(string='Date', default=fields.Date.today)
    day = fields.Char(string='Day')
    employee_timesheet_report_line_ids = fields.One2many('employee.timesheet.report.line',
                                                         'employee_timesheet_report_id',
                                                         string='Employee Timesheet Report Lines')

    @api.depends('date', 'employee_id')
    def _compute_name(self):
        for rec in self:
            if rec.date and rec.employee_id:
                name = rec.employee_id.name + ' - ' + str(rec.date)
                rec.write({'name': name})
            else:
                rec.name = ''

    @api.onchange('date', 'employee_id')
    def _onchange_date(self):
        if self.date:
            self.day = datetime.strptime(str(self.date), '%Y-%m-%d').strftime('%A')
        else:
            self.day = False

        if self.employee_timesheet_report_line_ids:
            self.employee_timesheet_report_line_ids = False

        if self.date and self.employee_id:
            timesheets = self.env['account.analytic.line'].search([
                ('employee_id', '=', self.employee_id.id),
                ('date', '=', self.date)
            ])

            new_lines = []
            for timesheet in timesheets:
                local_tz = pytz.timezone(
                    timesheet.employee_id.tz or 'UTC')
                if timesheet.date_start:
                    start_date_local = timesheet.date_start.replace(tzinfo=UTC).astimezone(local_tz)
                    start_time = start_date_local.time()
                else:
                    start_time = ''
                if timesheet.date_end:
                    end_date_local = timesheet.date_end.replace(tzinfo=UTC).astimezone(local_tz)
                    end_time = end_date_local.time()
                else:
                    end_time = ''
                new_lines.append((0, 0, {
                    'employee_id': timesheet.employee_id.id,
                    'project_id': timesheet.project_id.id,
                    'task_id': timesheet.task_id.id,
                    'start_time': start_time,
                    'end_time': end_time,
                    'hours_spent': timesheet.unit_amount,
                }))

            self.employee_timesheet_report_line_ids = new_lines


class EmployeeTimesheetReportLine(models.Model):
    _name = 'employee.timesheet.report.line'
    _description = 'Employee Timesheet Report Line'

    project_id = fields.Many2one('project.project', string='Project')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    task_id = fields.Many2one('project.task', string='Task')
    start_date = fields.Datetime(string='Start Date')
    start_time = fields.Char(string='Start Time', store=True)
    end_date = fields.Datetime(string='End Date')
    end_time = fields.Char(string='End Time', store=True)
    hours_spent = fields.Float(string='Hours Spent')
    employee_timesheet_report_id = fields.Many2one('employee.timesheet.report', string='Employee Timesheet Report')
