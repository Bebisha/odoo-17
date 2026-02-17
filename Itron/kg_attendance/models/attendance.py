from odoo import models, fields, api
from datetime import date, datetime, timedelta


class Attendance(models.Model):
    _name = 'kg.attendance'
    _description = "Model for Attendance"
    _rec_name = 'company_id'

    date = fields.Date('Date')
    company_id = fields.Many2one('res.company', 'Company')
    attendance_line_ids = fields.One2many('attendance.line', 'attendance_line_id', 'Attendance line')
    attendance_id = fields.Many2one('kg.attendance.report', 'Attendance line')

    @api.onchange('company_id')
    def _onchange_company_id(self):
        self.attendance_line_ids = False
        employee = self.env['hr.employee'].sudo().search([('company_id', '=', self.company_id.id)])

        attendance_lin = []
        for rec in employee:
            attendance_lin.append((0, 0, {
                'employee_name': rec.name,
                'employee_id': rec.id,
            }))
        self.attendance_line_ids = attendance_lin
    #
    # @api.model
    # def get_values(self):
    #
    #     current_date = fields.Date.today()
    #
    #     start_of_month = current_date.replace(day=1)  # Start of the current month
    #     end_of_month = (datetime(current_date.year, current_date.month, 1) + timedelta(days=32)).replace(
    #         day=1) - timedelta(days=1)  # End of the current month
    #
    #     companies = self.env['res.company'].search([])
    #     company_data = [{"id": company.id, "name": company.name} for company in companies]
    #     user = self.env.user
    #     is_admin = user.has_group('base.group_system')  # Check if the user is an admin
    #
    #     teams = self.env['project.team'].search([('timesheet_user_ids', '=', user.id)])
    #     current_company = user.company_id
    #     domain = [
    #         ('type', '=', 'late_arrival'),
    #         ('date_late', '=', current_date)
    #     ]
    #     team_member_ids = []
    #
    #     if not is_admin and teams:
    #         user_ids = teams.mapped('employee_ids').ids
    #         team_member_ids = self.env['hr.employee'].sudo().search([('user_id', 'in', user_ids)]).ids
    #
    #         domain.append(('employee_id', '=', team_member_ids))
    #
    #     elif not is_admin and not teams:
    #         # user_ids = teams.mapped('employee_ids').ids
    #         team_member_ids = self.env['hr.employee'].sudo().search([('user_id', '=', user.id)]).ids
    #
    #         domain.append(('employee_id', '=', team_member_ids))
    #
    #     else:
    #         team_member_ids = self.env['hr.employee'].sudo().search([]).ids
    #         domain.append(('employee_id', '=', team_member_ids))
    #
    #     # if current_company:
    #     #     domain.append(('company_id', '=', current_company.id))
    #
    #     late_requests = self.env['early.late.request'].search(
    #         domain
    #     )
    #     start_of_week = current_date - timedelta(days=current_date.weekday() + 1)  # Sunday
    #     if start_of_week > current_date:
    #         start_of_week -= timedelta(weeks=1)  # Adjust for the case when today is Sunday
    #
    #     end_of_week = start_of_week + timedelta(days=6)
    #     employee_data = []
    #     monthly = 0
    #     for request in late_requests:
    #         employee = request.employee_id
    #         late_requests_month = self.env['early.late.request'].search([
    #             ('type', '=', 'late_arrival'),
    #             ('employee_id', '=', employee.id),
    #             ('date_late', '>=', start_of_month),
    #             ('date_late', '<=', end_of_month)
    #         ])
    #         late_week = self.env['early.late.request'].search([
    #             ('type', '=', 'late_arrival'),
    #             ('employee_id', '=', employee.id),
    #             ('date_late', '>=', start_of_week),
    #             ('date_late', '<=', end_of_week)
    #         ])
    #         time_strings_month = late_requests_month.mapped('late_hrs')
    #         time_strings_week = late_week.mapped('late_hrs')
    #         hours_week = 0
    #         total_hours = 0
    #         total_minutes = 0
    #         minutes_week = 0
    #
    #         # Iterate through the time strings
    #         for time_str in time_strings_month:
    #             # Extract hours and minutes from the string
    #             parts = time_str.split(' and ')
    #             hours = int(parts[0].split(' ')[0])  # Extract hours
    #             minutes = int(parts[1].split(' ')[0])  # Extract minutes
    #
    #             # Add to total hours and minutes
    #             total_hours += hours
    #             total_minutes += minutes
    #
    #         # Convert total minutes to hours and minutes
    #         total_hours += total_minutes // 60
    #         total_minutes = total_minutes % 60
    #         for time_str in time_strings_week:
    #             # Extract hours and minutes from the string
    #             parts = time_str.split(' and ')
    #             hours = int(parts[0].split(' ')[0])  # Extract hours
    #             minutes = int(parts[1].split(' ')[0])  # Extract minutes
    #
    #             # Add to total hours and minutes
    #             hours_week += hours
    #             minutes_week += minutes
    #
    #         # Convert total minutes to hours and minutes
    #         hours_week += minutes_week // 60
    #         minutes_week = minutes_week % 60
    #
    #
    #         if request.type == 'late_arrival':
    #             employee_data.append({
    #                 "id": request.id,
    #                 "employee_id": employee.id,
    #                 "name": employee.name,
    #                 "company_id": employee.company_id.id,
    #                 "company_name": employee.company_id.name,
    #                 "late_by": request.late_hrs,
    #                 "arrival_time": request.time_string,
    #                 'week_late': f"{hours_week:02}:{minutes_week:02}",
    #                 'monthly_late': f"{total_hours}:{total_minutes:02}",
    #                 'late':{
    #                     'total_late':late_requests_month.ids,
    #                     'current_late':request.ids,
    #                     'week_late':late_week.ids
    #                       },
    #                 # "current_month": current_month,
    #             })
    #
    #     return ({
    #         "current_company_id": self.env.company.id,
    #         "companies": company_data,
    #         "employees": employee_data,
    #         'tree_view': self.env.ref('kg_attendance.early_late_request_tree').id
    #
    #     })
    #

class AttendanceLine(models.Model):
    _name = 'attendance.line'
    _description = "Model for Attendance Line"

    employee_name = fields.Char('Employee Name')
    employee_id = fields.Char('Employee ID')
    time_in = fields.Datetime('Time In')
    time_out = fields.Datetime('Time Out')
    attendance_line_id = fields.Many2one('kg.attendance', 'Attendance Reference')
    attendance_id = fields.Many2one('kg.attendance.report', 'Attendance line')
