# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from collections import defaultdict
from odoo import api, models, fields, _


class TimesheetAnalysisReport(models.Model):
    _name = 'timesheet.analysis.report'
    _description = 'Timesheet Analysis Report'

    employee_id = fields.Many2one('hr.employee', string='Employee')
    company_id = fields.Many2one('res.company', string='Company', related='employee_id.company_id')
    timesheet_id = fields.Many2one('account.analytic.line', string='Timesheet')
    date = fields.Date(string='Date')
    hours_per_day = fields.Float(string='Hours')

    @api.depends('employee_id', 'timesheet_id')
    def _compute_hours_per_day(self):
        for timesheet in self:
            if timesheet.date:
                timesheets = self.env['account.analytic.line'].search([
                    ('employee_id', '=', timesheet.employee_id.id),
                    ('date', '=', timesheet.date)
                ])
                total_hours = sum(timesheet.unit_amount for timesheet in timesheets)
                timesheet.hours_per_day = str(total_hours)
            else:
                timesheet.hours_per_day = '0'

    def load_timesheet_details(self):
        user = self.env.user
        teams = self.env['project.team'].sudo().search(
            [('timesheet_user_ids', '=', user.id)])
        user_ids = teams.mapped('employee_ids').ids
        is_cto = user.has_group('kg_timeoff_dashboard.group_admin_india_dashboard')
        is_admin = user.has_group('base.group_system')

        if is_admin:
            employees = self.env['hr.employee'].sudo().search([])

        elif is_cto:
            employees = self.env['hr.employee'].sudo().search(
                [('company_id', '=', self.env.company.id), ('exclude_from_timesheet', '=', False)])
        elif user.has_group('hr_timesheet.group_timesheet_manager'):
            employees = self.env['hr.employee'].sudo().search(
                [('exclude_from_timesheet', '=', False)])
        elif user.has_group('hr_timesheet.group_hr_timesheet_approver'):
            employees = self.env['hr.employee'].sudo().search(
                [('user_id', 'in', user_ids), ('exclude_from_timesheet', '=', False),
                 ('company_id', '=', self.env.company.id)])

        elif user.has_group('hr_timesheet.group_hr_timesheet_user'):
            employees = self.env['hr.employee'].sudo().search(
                [('user_id', '=', user.id), ('exclude_from_timesheet', '=', False)])



        else:
            employees = self.env['hr.employee'].sudo().search([])

        domain_list = []
        dates = []

        for employee in employees:
            first_of_month = datetime.today().replace(day=1).date()
            today = datetime.today().date()

            timesheet_data = []

            timesheet_data = self.env['account.analytic.line'].sudo().search([
                ('employee_id', '=', employee.id),
                # ('employee_id.user_id', '=', user.id),
                ('date', '>=', first_of_month)
            ])

            # if user.has_group('hr_timesheet.group_hr_timesheet_approver'):
            #     timesheet_data = self.env['account.analytic.line'].sudo().search([
            #         ('employee_id', '=', employee.id),
            #         ('project_id', '!=', False),
            #         ('project_id.project_team_id.timesheet_user_ids', 'in', [user.id]),
            #         '|',
            #         ('project_id.privacy_visibility', '!=', 'followers'),
            #         ('project_id.message_partner_ids', 'in', [user.partner_id.id]),
            #         ('date', '>=', first_of_month)
            #     ])
            #
            # if user.has_group('hr_timesheet.group_timesheet_manager'):
            #     timesheet_data = self.env['account.analytic.line'].sudo().search([
            #         ('employee_id', '=', employee.id),
            #         ('project_id', '!=', False),
            #         ('date', '>=', first_of_month)
            #     ])

            hours_by_date = defaultdict(float)

            if timesheet_data:
                for timesheet in timesheet_data:
                    hours_by_date[timesheet.date] += timesheet.unit_amount

            current_date = first_of_month
            while current_date <= today:
                if current_date.weekday() != 5:
                    if current_date not in hours_by_date:
                        hours_by_date[current_date] = 0
                current_date += timedelta(days=1)

            for date, total_hours in hours_by_date.items():
                if date not in dates:
                    dates.append(date)

                is_leave = self.env['hr.leave'].sudo().search_count([
                    ('employee_id', '=', employee.id),
                    ('state', '=', 'validate'),  # Approved leave
                    ('request_date_from', '<=', date),
                    ('request_date_to', '>=', date)
                ]) > 0

                record = self.env['timesheet.analysis.report'].sudo().create({
                    'employee_id': employee.id,
                    'date': date,
                    'hours_per_day': total_hours,
                })
                domain_list.append(record.id)

        return {
            'name': _('Employee Timesheet'),
            'view_type': 'form',
            'view_mode': 'pivot,tree',
            'domain': [('id', 'in', domain_list)],
            'res_model': 'timesheet.analysis.report',
            'type': 'ir.actions.act_window',
            'target': 'main',
        }
    def view_timesheet_pivot(self):
        return {
            'name': _('Employee Timesheet'),
            'view_type': 'tree',
            'view_mode': 'tree',
            'domain': [
                ('date', '=', self.date),
                ('employee_id', '=', self.employee_id.id),
            ],

            'res_model': 'account.analytic.line',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'create': False,

            },
        }