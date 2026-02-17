# -*- coding: utf-8 -*-
import pytz
from pytz import timezone, UTC
from odoo import api, models, fields, _


class EmployeeTimesheetReport(models.TransientModel):
    _name = 'employee.timesheet.report.wizard'
    _description = 'Employee Timesheet Report Wizard'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    date = fields.Date(string='Date', default=fields.Date.today, required=True)

    def action_view_timesheet(self):
        """ Action to view the timesheet of selected employee on selected date """
        domain_list = []
        timesheets = self.env['account.analytic.line'].search([
            ('employee_id', '=', self.employee_id.id),
            ('date', '=', self.date)
        ])
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

            record = self.env['employee.timesheet.report.line'].sudo().create({
                'employee_id': timesheet.employee_id.id,
                'project_id': timesheet.project_id.id,
                'task_id': timesheet.task_id.id,
                'start_time': start_time,
                'end_time': end_time,
                'hours_spent': timesheet.unit_amount,
            })
            domain_list.append(record.id)

        return {
            'name': _('Employee Timesheet Report'),
            'view_type': 'tree',
            'view_mode': 'tree',
            'domain': [('id', 'in', domain_list)],
            'context': {
                'search_default_groupby_employee_id': 1,
            },
            'res_model': 'employee.timesheet.report.line',
            'type': 'ir.actions.act_window',
            'target': 'main',
        }
