from odoo import api, models
from datetime import date, timedelta
import calendar

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    @api.model
    def missing_timesheet(self, company_id=None, team_id=None):
        user = self.env.user
        is_admin = user.has_group('base.group_system')
        today = date.today()
        companies = self.env.user.company_ids

        if company_id:
            company = self.env['res.company'].browse(company_id)
        else:
            company = self.env.company

        # Determine target date
        if company.country_code in ['IN', 'AE', 'US']:
            if today.weekday() == 0:
                target_date = today - timedelta(days=3)
            elif today.weekday() in [5, 6]:
                target_date = today - timedelta(days=(1 if today.weekday() == 5 else 2))
            else:
                target_date = today - timedelta(days=1)
        else:
            if today.weekday() == 6:
                target_date = today - timedelta(days=3)
            elif today.weekday() in [5, 4]:
                target_date = today - timedelta(days=(2 if today.weekday() == 5 else 1))
            else:
                target_date = today - timedelta(days=1)

        domain = [
            ('date_start', '>=', target_date),
            ('date_end', '<=', target_date),
        ]

        if company_id:
            domain.append(('company_id', '=', company_id))

        if team_id:
            domain += ['|',
                       ('project_id.project_team_id', '=', team_id),
                       ('employee_id.project_team_id', '=', team_id)]
            # domain.append(('project_id.project_team_id', '=', team_id))

        # Determine relevant employees
        team_member_ids = []
        is_cto = user.has_group('kg_timeoff_dashboard.group_admin_india_dashboard')


        if is_cto:
            employees = self.env['hr.employee'].sudo().search([
                ('company_id', '=', self.env.company.id),
                ('exclude_from_timesheet', '=', False)
            ])

        elif not is_admin:
            teams = self.env['project.team'].sudo().search([('timesheet_user_ids', '=', user.id)])
            user_ids = teams.mapped('employee_ids').ids
            employees = self.env['hr.employee'].sudo().search([
                ('user_id', 'in', user_ids or [user.id]),
                ('company_id', 'in', companies.ids),
                ('exclude_from_timesheet', '=', False)
            ])
        else:
            employees = self.env['hr.employee'].sudo().search([
                ('exclude_from_timesheet', '=', False)
            ])

        if employees:
            domain.append(('employee_id', 'in', employees.ids))

        timesheets = self.env['account.analytic.line'].sudo().search(domain)

        timesheet_dict = {}
        for ts in timesheets:
            timesheet_dict.setdefault(ts.employee_id.id, self.env['account.analytic.line'])
            timesheet_dict[ts.employee_id.id] |= ts

        missing_timesheets = []
        for employee in employees:
            date_and_day = f"{target_date.strftime('%d/%m/%Y')} ({calendar.day_name[target_date.weekday()]})"
            leave_records = self.env['hr.leave'].sudo().search([
                ('employee_id', '=', employee.id),
                ('request_date_from', '<=', target_date),
                ('request_date_to', '>=', target_date),
            ])

            employee_data = {
                'id': employee.id,
                'company_id': employee.company_id.id,
                'team_id': employee.project_team_id.id if employee.project_team_id else None,
                'name': employee.name,
                'leave': leave_records,
                'date_and_day': date_and_day,
                'timesheet_submitted': False,
                'timesheet_partialy_submitted': False,
                'on_leave': False,
                'half_day': False,
                'hour_spent': "00:00",
                'timesheets': [],
            }
            print("employee ata",employee_data)

            if employee.id in timesheet_dict:
                emp_ts = timesheet_dict[employee.id]
                total_hours = sum(emp_ts.mapped('unit_amount'))
                hours = int(total_hours)
                minutes = int((total_hours - hours) * 60)
                formatted_hours = f"{hours:02}:{minutes:02}"
                employee_data['hour_spent'] = formatted_hours
                employee_data['timesheets'] = emp_ts.ids

                if 0 < total_hours < 8:
                    employee_data['timesheet_partialy_submitted'] = True
                    if any(l.request_unit_half for l in leave_records):
                        employee_data['half_day'] = True
                elif total_hours >= 8:
                    employee_data['timesheet_submitted'] = True
            else:
                if leave_records:
                    if any(l.request_unit_half for l in leave_records):
                        employee_data['half_day'] = True
                    else:
                        employee_data['on_leave'] = True

            missing_timesheets.append(employee_data)

        company_data = [{'id': c.id, 'name': c.name, 'country_code': c.country_code} for c in companies]
        team_data = [{'id': t.id, 'name': t.name} for t in self.env['project.team'].sudo().search([])]
        print("team_dataaaaaaaaaaaaaaaaaa",team_data)

        return {
            'missing_timesheets': missing_timesheets,
            'company_data': company_data,
            'team_data': team_data,
            'current_company_id': self.env.company.id,
        }
