# -*- coding: utf-8 -*-
from odoo import models, fields, _
from datetime import datetime, timedelta
from collections import defaultdict


class EmployeeTimesheetDateWise(models.TransientModel):
    """ Model for employee timesheet report organized by date. """
    _name = 'employee.timesheet.date.wise.wizard'
    _description = 'employee.timesheet.date.wise.wizard'

    date_from = fields.Date(string='Date From', required=True)
    date_to = fields.Date(string='Date To', required=True)
    company_id = fields.Many2one('res.company', required=True, string='Company')

    def action_confirm(self):
        """ Function to display the employee timesheet report by date """
        user = self.env.user
        employees = self.env['hr.employee'].sudo().search([
            ('exclude_from_timesheet', '=', False),
            ('company_id', '=', self.company_id.id)
        ])
        domain_list = []
        dates = []

        for employee in employees:
            timesheet_data = []
            if user.has_group('base.group_user'):
                timesheet_data = self.env['account.analytic.line'].search([
                    ('employee_id', '=', employee.id),
                    ('employee_id.user_id', '=', user.id),
                    ('date', '>=', self.date_from),
                    ('date', '<=', self.date_to),
                    ('company_id', '=', self.company_id.id)
                ])

            if user.has_group('hr_timesheet.group_hr_timesheet_approver'):
                timesheet_data = self.env['account.analytic.line'].search([
                    ('employee_id', '=', employee.id),
                    ('project_id', '!=', False),
                    ('project_id.project_team_id.timesheet_user_ids', 'in', [user.id]),
                    '|',
                    ('project_id.privacy_visibility', '!=', 'followers'),
                    ('project_id.message_partner_ids', 'in', [user.partner_id.id]),
                    ('date', '>=', self.date_from),
                    ('date', '<=', self.date_to),
                    ('company_id', '=', self.company_id.id)
                ])

            if user.has_group('hr_timesheet.group_timesheet_manager'):
                timesheet_data = self.env['account.analytic.line'].sudo().search([
                    ('employee_id', '=', employee.id),
                    ('project_id', '!=', False),
                    ('date', '>=', self.date_from),
                    ('date', '<=', self.date_to),
                    ('company_id', '=', self.company_id.id)
                ])

            hours_by_date = defaultdict(float)
            if timesheet_data:
                for timesheet in timesheet_data:
                    hours_by_date[timesheet.date] += timesheet.unit_amount

            current_date = self.date_from
            while current_date <= self.date_to:
                if current_date.weekday() != 5:
                    if current_date not in hours_by_date:
                        hours_by_date[current_date] = 0
                current_date += timedelta(days=1)

            for date, total_hours in hours_by_date.items():
                if date not in dates:
                    dates.append(date)
                record = self.env['timesheet.analysis.report'].sudo().create({
                    'employee_id': employee.id,
                    'date': date,
                    'hours_per_day': total_hours,
                })
                domain_list.append(record.id)

        return {
            'name': _('Employee Timesheet Date Wise'),
            'view_type': 'form',
            'view_mode': 'pivot,tree',
            'domain': [('id', 'in', domain_list)],
            'res_model': 'timesheet.analysis.report',
            'type': 'ir.actions.act_window',
            'target': 'main',
        }