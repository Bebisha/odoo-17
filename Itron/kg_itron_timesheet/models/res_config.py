import ast
from datetime import date, timedelta, datetime

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ResCompanyInherit(models.Model):
    _inherit = 'res.company'

    timesheet_employee_ids = fields.Many2many('hr.employee',string="Timesheet Report")


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    timesheet_employee_ids = fields.Many2many('hr.employee', string="Timesheet Employees", relation='timesheet_rel_hr',
                                              related="company_id.timesheet_employee_ids",
                                              help="Select users for generating the missing timesheet report.",readonly=False)

    # def get_values(self):
    #     res = super(ResConfigSettings, self).get_values()
    #     params = self.env['ir.config_parameter'].sudo()
    #
    #     timesheet_employee_ids_str = params.get_param('kg_itron_timesheet.timesheet_employee_ids', default=[])
    #
    #     timesheet_employee_ids = eval(timesheet_employee_ids_str) if timesheet_employee_ids_str else []
    #
    #     res.update(
    #         timesheet_employee_ids=[(6, 0, timesheet_employee_ids)],
    #     )
    #     return res
    #
    # def set_values(self):
    #     super(ResConfigSettings, self).set_values()
    #
    #     timesheet_employee_ids = self.timesheet_employee_ids.ids if self.timesheet_employee_ids else []
    #
    #     self.env['ir.config_parameter'].sudo().set_param("kg_itron_timesheet.timesheet_employee_ids",
    #                                                      str(timesheet_employee_ids))

    @api.model
    def send_missing_timesheet_email(self, time=None):
        """Send emails to employees with missing or incomplete timesheets and their leave details."""
        selected_employees = self.env.user.company_ids.mapped('timesheet_employee_ids').ids
        print(selected_employees, 'ddddddddddddddddd')
        if not selected_employees:
            raise ValidationError("No employees selected. Please select at least one employee.")

        employees = self.env['hr.employee'].browse(selected_employees)
        if not employees:
            raise ValidationError("No valid employees found.")

        admin_users = self.env.ref("kg_attendance.all_approval_access").users

        admin_emails = ', '.join(admin_users.mapped('email'))

        yesterday = date.today() - timedelta(days=1)
        formatted_date = yesterday.strftime('%d-%m-%Y')
        current_year = date.today().year
        start_date = f"{current_year}-01-01"
        end_date = f"{current_year}-12-31"

        email_content = "<p>Dear Sir,</p>"
        email_content += f"<p>The following employees have missing or incomplete timesheets for ({formatted_date}), yesterday:</p>"
        companies = employees.mapped('company_id')
        print(companies, 'companies')
        company_employee_data = {}

        # Loop through each company and map employees
        for company in companies:
            missing_timesheets = []
            company_employees = employees.filtered(lambda e: e.company_id == company)
            company_employee_data[company] = {}

            for employee in company_employees:
                calendar = employee.resource_calendar_id
                if not calendar:
                    continue

                print(calendar.attendance_ids.mapped('dayofweek'), 'dddddddddddd')
                unique_sorted_list = sorted(set(calendar.attendance_ids.mapped('dayofweek')))

                print(unique_sorted_list)
                closest_day = None
                closest_date = None
                today = date.today()

                for day in unique_sorted_list:
                    current_day = today.weekday()  # Current day as an integer (0 = Monday)
                    day = int(day)
                    if current_day > day:
                        # If today is after the target day, return the closest target day in the past
                        delta_days = current_day - day
                        target_date = today - timedelta(days=delta_days)
                        if closest_date is None or target_date > closest_date:
                            closest_day = day
                            closest_date = target_date
                    elif current_day < day:
                        # If today is before the target day, check for the previous week
                        delta_days = current_day - day + 7
                        target_date = today - timedelta(days=delta_days)
                        if closest_date is None or target_date > closest_date:
                            closest_day = day
                            closest_date = target_date
                print(closest_date, 'sssssssssssssssssss', employee.name)

                if closest_date == yesterday:
                    timesheets = self.env['account.analytic.line'].search([
                        ('employee_id', '=', employee.id),
                        ('date', '=', closest_date)
                    ])

                    allocation_domain = [
                        ('employee_id', '=', employee.id),
                        ('date_from', '>=', start_date),
                        ('date_to', '<=', end_date)
                    ]

                    sick_leave_type = self.env['hr.leave.type'].search([('time_off_type', '=', 'is_sick')], limit=1)
                    total_sick_leaves = sum(leave.number_of_days for leave in self.env['hr.leave'].search(
                        allocation_domain + [('holiday_status_id', '=', sick_leave_type.id)]
                    ))

                    sick_leave_allocation = self.env['hr.leave.allocation'].search(
                        allocation_domain + [('holiday_status_id', '=', sick_leave_type.id)]
                    )
                    total_sick_allocation = sum(allocation.number_of_days for allocation in sick_leave_allocation)

                    # Casual/Annual leave based on country
                    if employee.company_id.country_code == 'IN':
                        casual_leave_type = self.env['hr.leave.type'].search([('time_off_type', '=', 'is_casual')],
                                                                             limit=1)
                    else:
                        casual_leave_type = self.env['hr.leave.type'].search([('time_off_type', '=', 'is_annual')],
                                                                             limit=1)

                    total_casual_leave = sum(leave.number_of_days for leave in self.env['hr.leave'].search(
                        allocation_domain + [('holiday_status_id', '=', casual_leave_type.id)]
                    ))

                    casual_leave_allocation = self.env['hr.leave.allocation'].search(
                        allocation_domain + [('holiday_status_id', '=', casual_leave_type.id)]
                    )
                    total_casual_allocation = sum(allocation.number_of_days for allocation in casual_leave_allocation)

                    # Unpaid leave
                    unpaid_leave_type = self.env['hr.leave.type'].search([('time_off_type', '=', 'is_unpaid')], limit=1)
                    total_unpaid_leave = sum(leave.number_of_days for leave in self.env['hr.leave'].search(
                        allocation_domain + [('holiday_status_id', '=', unpaid_leave_type.id)]
                    ))

                    unpaid_leave_allocation = self.env['hr.leave.allocation'].search(
                        allocation_domain + [('holiday_status_id', '=', unpaid_leave_type.id)]
                    )
                    total_unpaid_allocation = sum(allocation.number_of_days for allocation in unpaid_leave_allocation)

                    total_allocation = sum(
                        allocation.number_of_days for allocation in self.env['hr.leave.allocation'].search(
                            allocation_domain + [
                                (
                                    'holiday_status_id', 'in',
                                    [sick_leave_type.id, casual_leave_type.id, unpaid_leave_type.id])
                            ]
                        ))

                    sick_leaves = self.env['hr.leave'].sudo().search([
                        ('employee_id', '=', employee.id),
                        ('holiday_status_id', '=', sick_leave_type.id),
                        ('date_from', '>=', f'{current_year}-01-01'),
                        ('state', '=', 'validate')
                    ])
                    print(sick_leaves, "sss")
                    casual_leaves = self.env['hr.leave'].sudo().search([
                        ('employee_id', '=', employee.id),
                        ('holiday_status_id', '=', casual_leave_type.id),
                        ('date_from', '>=', f'{current_year}-01-01'),
                        ('state', '=', 'validate')
                    ])
                    print(casual_leaves, "dddddd")
                    unpaid_leaves = self.env['hr.leave'].sudo().search([
                        ('employee_id', '=', employee.id),
                        ('holiday_status_id', '=', unpaid_leave_type.id),
                        ('date_from', '>=', f'{current_year}-01-01'),
                        ('state', '=', 'validate')
                    ])
                    sick_leave_count = sum(allocation.number_of_days for allocation in sick_leaves)

                    casual_leave_count = sum(allocation.number_of_days for allocation in casual_leaves)

                    unpaid_leave_count = sum(allocation.number_of_days for allocation in unpaid_leaves)

                    remaining_leaves = max(0,
                                           total_allocation - (
                                                       sick_leave_count + casual_leave_count + unpaid_leave_count))
                    total_allocation = total_sick_allocation + total_casual_allocation
                    total_leave = sick_leave_count + casual_leave_count + unpaid_leave_count
                    company_data = company_employee_data.get(company, {})
                    if timesheets:
                        for rec in timesheets:
                            if rec.unit_amount <= 8:
                                company_data[employee] = {
                                    'timesheet_submitted': True,
                                    'hour_spent': rec.unit_amount,
                                    'sick_leave': f"{sick_leave_count}/{total_sick_allocation}",
                                    'casual_leaves': f"{casual_leave_count}/{total_casual_allocation}",
                                    'unpaid_leave': unpaid_leave_count,
                                    'total_leave_allocation': f"{total_leave}/{total_allocation}",
                                    'remaining_leaves': remaining_leaves
                                }

                    else:
                        # Employee hasn't submitted timesheet
                        if employee in company_employee_data:
                            company_data[employee].update({
                                'timesheet_submitted': False,
                                'hour_spent': 0,
                                'sick_leave': f"{sick_leave_count}/{total_sick_allocation}",
                                'casual_leaves': f"{casual_leave_count}/{total_casual_allocation}",
                                'unpaid_leave': unpaid_leave_count,
                                'total_leave_allocation': f"{total_leave}/{total_allocation}",
                                'remaining_leaves': remaining_leaves
                            })
                        else:
                            company_data[employee] = {
                                'timesheet_submitted': False,
                                'hour_spent': 0,
                                'sick_leave': f"{sick_leave_count}/{total_sick_allocation}",
                                'casual_leaves': f"{casual_leave_count}/{total_casual_allocation}",
                                'unpaid_leave': unpaid_leave_count,
                                'total_leave_allocation': f"{total_leave}/{total_allocation}",
                                'remaining_leaves': remaining_leaves
                            }
                        company_employee_data[company] = company_data
            if not company_employee_data[company]:
                del company_employee_data[company]
        for company, requests in company_employee_data.items():
            if company.country_code == 'IN':
                email_content += "<table border='1'><tr><th>Employee</th><th>Timesheet</th><th>Hours Spent</th><th>Sick Leaves</th><th>Casual Leaves</th><th>Unpaid Leaves</th><th>Total Leaves</th><th>Remaining Leaves</th></tr>"
            else:
                email_content += "<table border='1'><tr><th>Employee</th><th>Timesheet</th><th>Hours Spent</th><th>Sick Leaves</th><th>Annual Leaves</th><th>Unpaid Leaves</th><th>Total Leaves</th><th>Remaining Leaves</th></tr>"

            email_content += f"<h3><u>{company.name}</u></h3>"
            for employee, emp_data in requests.items():
                print(employee, emp_data, 'ddddd')
                email_content += f"<tr><td>{employee.name}</td>"

                # Iterate over the emp_data dictionary correctly
                for time, timesheets in emp_data.items():  # Corrected this line
                    print(time, timesheets, 'timesheets')
                    if isinstance(timesheets, bool):
                        timesheets = '<span style="color:green; font-size: 20px;text-align:center; display:block;">&#10004;</span>' if timesheets else '<span style="color:red; font-size: 10px;text-align:center; display:block;">&#10060;</span>'
                    email_content += f"<td style='text-align:center;    '>{timesheets}</td>"  # Display the value of timesheets instead of the time (which is the key)
                email_content += "</tr>"

        print(company_employee_data, 'company_employee_data')

        email_content += "</table>"

        mail_values = {
            'subject': 'Missing or Incomplete Timesheets and Leave Status',
            'body_html': email_content,
            'email_to': admin_emails,
        }
        mail = self.env['mail.mail'].create(mail_values)
        mail.send()