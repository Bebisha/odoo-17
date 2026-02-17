from datetime import date

from odoo import models, api,fields
from odoo.http import request
import re
from datetime import date, datetime, timedelta



class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    exclude_in_dashboard = fields.Boolean(string="Exclude from Dashboard")
    exclude_from_timesheet = fields.Boolean(string="Exclude from Timesheet")

    @api.model
    def get_employee_leave_data(self):
        """ Get current year leave allocations."""
        current_year = date.today().year
        user = self.env.user
        employees = []
        if user.has_group('base.group_user'):
            employees = self.env['hr.employee'].sudo().search([
                ('user_id', '=', user.id),
                ('exclude_in_dashboard', '=', False)
            ])

        if user.has_group('hr_holidays.group_hr_holidays_user'):
            employees = self.env['hr.employee'].search([
                '|',
                ('user_id', '=', user.id),
                ('leave_manager_id', '=', user.id),
                ('exclude_in_dashboard', '=', False)
            ])

        if user.has_group('hr_holidays.group_hr_holidays_manager') or user.has_group(
                'kg_timeoff_dashboard.group_admin_india_dashboard'):
            employees = self.env['hr.employee'].sudo().search([
                ('exclude_in_dashboard', '=', False)
            ])
        employee_data = []

        for employee in employees:
            joining_date = employee.date_joining or date(current_year, 1, 1)
            start_date = max(joining_date, date(current_year, 1, 1))
            end_date = date(current_year + 1, 12, 31)
            today = fields.Date.today()
            leave_allocation_domain = [
                ('employee_id', '=', employee.id),
                ('state', '=', 'validate'),
                '|', ('date_from', '>=', start_date),
                ('date_to', '<=', end_date),
                '|', ('date_to', '>=', today),
                ('date_to', '=', False),
            ]
            # leave_allocation_domain = [
            #     ('employee_id', '=', employee.id),
            #     ('state', '=', 'validate'),
            #     ('date_from', '<=', today),
            #     '|',
            #     ('date_to', '=', False),
            #     ('date_to', '>=', today),
            # ]
            # # print(leave_allocation_domain_new,'leave_allocation_domain_new')
            # print(leave_allocation_domain,'leave_allocation_domain')
            leave_domain = [
                ('employee_id', '=', employee.id),
                ('state', '=', 'validate'),
            ]

            sick_leave_type = self.env['hr.leave.type'].sudo().search([('time_off_type', '=', 'is_sick')])

            sick_leave_allocation = self.env['hr.leave.allocation'].sudo().search(
                leave_allocation_domain + [
                    ('holiday_status_id', 'in', [sick_leave.id for sick_leave in sick_leave_type])]
            )

            if sick_leave_allocation:
                start_date_alloc_sick = min(sick_leave_allocation.mapped('date_from'))
                end_date_alloc_sick = max(sick_leave_allocation.mapped('date_to'))
            else:
                start_date_alloc_sick = False
                end_date_alloc_sick = False

            total_sick_leaves = sum(
                leave.number_of_days for leave in self.env['hr.leave'].sudo().search(
                    leave_domain + [('holiday_status_id', 'in', [sick_leave.id for sick_leave in sick_leave_type]),
                                    ('date_from', '>=', start_date_alloc_sick), ('date_to', '<=', end_date_alloc_sick)]
                )
            )

            total_sick_allocation = sum(allocation.number_of_days for allocation in sick_leave_allocation)

            if employee.company_id.country_code == 'IN':
                casual_leave_type = self.env['hr.leave.type'].sudo().search([('time_off_type', '=', 'is_casual')])
            else:
                casual_leave_type = self.env['hr.leave.type'].sudo().search([('time_off_type', '=', 'is_annual')])

                all_annual_allocations = self.env['hr.leave.allocation'].sudo().search([
                    ('employee_id', '=', employee.id),
                    ('holiday_status_id', 'in', casual_leave_type.ids),
                    ('state', '=', 'validate'),
                ])

                # 3. Get only expired allocations (date_to < today)
                expired_annual_allocations = all_annual_allocations.filtered(
                    lambda alloc: alloc.date_to and alloc.date_to < today
                )

                # 4. Get all validated annual leaves from hr.leave
                annual_leaves = self.env['hr.leave'].sudo().search([
                    ('employee_id', '=', employee.id),
                    ('holiday_status_id', 'in', casual_leave_type.ids),
                    ('state', '=', 'validate'),
                ])

                # 5. Count days
                total_allocation_days = sum(all_annual_allocations.mapped('number_of_days'))
                total_expired_allocation_days = sum(expired_annual_allocations.mapped('number_of_days'))
                total_leave_days = sum(annual_leaves.mapped('number_of_days'))
                if total_expired_allocation_days <= total_leave_days:
                    total_casual_leave = total_leave_days - total_expired_allocation_days
                else:
                    total_casual_leave = 0

                # 6. Print summary


            casual_leave_allocation = self.env['hr.leave.allocation'].sudo().search(
                leave_allocation_domain + [
                    ('holiday_status_id', 'in', [casual_leave.id for casual_leave in casual_leave_type])]
            )


            if casual_leave_allocation:
                start_date_alloc_casual = min(casual_leave_allocation.mapped('date_from'))
                end_date_alloc_casual = max(casual_leave_allocation.mapped('date_to'))
            else:
                start_date_alloc_casual = False
                end_date_alloc_casual = False



            total_casual_leave = sum(leave.number_of_days for leave in self.env['hr.leave'].sudo().search(
                leave_domain + [('holiday_status_id', 'in', [casual_leave.id for casual_leave in casual_leave_type]),
                                ('date_from', '>=', start_date_alloc_casual), ('date_to', '<=', end_date_alloc_casual)]
            ))
            # total_casual_leave_new = sum(leave.number_of_days for leave in self.env['hr.leave'].sudo().search(
            #     leave_domain + [('holiday_status_id', 'in', [casual_leave.id for casual_leave in casual_leave_type]),
            #                     ]
            # ))
            # total_casual_leave_new = sum(leave.number_of_days for leave in self.env['hr.leave'].sudo().search(
            #     leave_domain + [('holiday_status_id', 'in', [casual_leave.id for casual_leave in casual_leave_type]),
            #                     ]
            # ))
            # print(total_casual_leave,employee.name,casual_leave_type,'total_casual_leave')

            total_casual_allocation = sum(allocation.number_of_days for allocation in casual_leave_allocation)
            total_casual_allocation = round(
                sum(allocation.number_of_days for allocation in casual_leave_allocation), 2
            )

            unpaid_leave_type = self.env['hr.leave.type'].sudo().search([('time_off_type', '=', 'is_unpaid'),('active','=', True)])
            total_unpaid_leave = sum(leave.number_of_days for leave in self.env['hr.leave'].sudo().search(
                leave_domain + [('holiday_status_id', 'in', unpaid_leave_type.ids), ('date_from', '>=', start_date),
                                ('date_to', '<=', end_date)]
            ))
            unpaid_leave_allocation = self.env['hr.leave.allocation'].sudo().search(
                leave_allocation_domain + [('holiday_status_id', 'in', unpaid_leave_type.ids)]
            )
            total_unpaid_allocation = sum(allocation.number_of_days for allocation in unpaid_leave_allocation)

            total_allocation = sum(
                allocation.number_of_days for allocation in self.env['hr.leave.allocation'].sudo().search(
                    leave_allocation_domain + [
                        ('holiday_status_id', 'in',
                         [sick_leave.id for sick_leave in sick_leave_type] + [casual_leave.id for casual_leave in
                                                                              casual_leave_type] + [
                             unpaid_leave.id for unpaid_leave in unpaid_leave_type])
                    ]
                )
            )
            total_allocation_new = sum(
                allocation.number_of_days for allocation in self.env['hr.leave.allocation'].sudo().search(
                    [('employee_id', '=', employee.id),]
                )
            )

            if employee.company_id.country_code != 'IN':


                all_annual_allocations = self.env['hr.leave.allocation'].sudo().search([
                    ('employee_id', '=', employee.id),
                    ('holiday_status_id', 'in', casual_leave_type.ids),
                    ('state', '=', 'validate'),
                ])

                expired_annual_allocations = all_annual_allocations.filtered(
                    lambda alloc: alloc.date_to and alloc.date_to < today
                )

                annual_leaves = self.env['hr.leave'].sudo().search([
                    ('employee_id', '=', employee.id),
                    ('holiday_status_id', 'in', casual_leave_type.ids),
                    ('state', '=', 'validate'),
                ])

                total_allocation_days = sum(all_annual_allocations.mapped('number_of_days'))
                total_expired_allocation_days = sum(expired_annual_allocations.mapped('number_of_days'))
                total_leave_days = sum(annual_leaves.mapped('number_of_days'))
                if total_expired_allocation_days <= total_leave_days:
                    total_casual_leave = total_leave_days - total_expired_allocation_days
                else:
                    total_casual_leave = 0
            today = date.today()

            valid_allocations = casual_leave_allocation.filtered(
                lambda alloc: alloc.date_from <= today <= alloc.date_to
            )

            valid_casual_leave_types = valid_allocations.mapped('holiday_status_id')

            start_date_alloc_casual = min(valid_allocations.mapped('date_from')) if valid_allocations else None
            end_date_alloc_casual = max(valid_allocations.mapped('date_to')) if valid_allocations else None

            casual_leaves = self.env['hr.leave'].sudo().search([
                *leave_domain,
                ('holiday_status_id', 'in', valid_casual_leave_types.ids),
                ('date_from', '>=', start_date_alloc_casual),
                ('date_to', '<=', end_date_alloc_casual),
            ]).ids

            employee_data.append({
                'id': employee.id,
                'name': employee.name,
                'company_id': employee.company_id.id,
                'total_sick_leaves': total_sick_leaves,
                'total_sick_allocation': total_sick_allocation,
                'total_casual_leave': total_casual_leave,
                'total_casual_allocation': total_casual_allocation,
                'total_unpaid_leave': total_unpaid_leave,
                'total_unpaid_allocation': total_unpaid_allocation,
                'total_leave_allocation': total_sick_allocation + total_casual_allocation + total_unpaid_allocation,
                'total_leave': total_sick_leaves + total_casual_leave + total_unpaid_leave,
                'remaining_allocation': total_allocation - (
                        total_sick_leaves + total_casual_leave
                ),
                'total_allocation': max(0, total_allocation - (
                        total_sick_leaves + total_casual_leave)),
                'leaves': {
                    'sick': self.env['hr.leave'].sudo().search(
                        leave_domain + [
                            ('holiday_status_id', 'in', [sick_leave.id for sick_leave in sick_leave_type]),
                            ('date_from', '>=', start_date_alloc_sick),
                            ('date_to', '<=', end_date_alloc_sick)]).ids,




                    'casual': casual_leaves,
                    'unpaid': self.env['hr.leave'].sudo().search(
                        leave_domain + [
                            ('holiday_status_id', 'in', [unpaid_leave.id for unpaid_leave in unpaid_leave_type]),
                            ('date_from', '>=', start_date), ('date_to', '<=', end_date)]).ids
                }
            })
        companies = self.env.user.company_ids
        company_data = [{'id': company.id, 'name': company.name, 'country_code': company.country_code} for company in
                        companies]

        return {
            'employee_data': employee_data,
            'company_data': company_data,
            'current_company_id': self.env.company.id,

        }

    @api.model
    def get_values(self, employee_id=None, **kwargs):
        start_date = kwargs.get('start_date')
        current_date = fields.Date.today()

        start_of_month = current_date.replace(day=1)
        end_of_month = (datetime(current_date.year, current_date.month, 1) + timedelta(days=32)).replace(
            day=1) - timedelta(days=1)

        user = self.env.user
        is_admin = user.has_group('base.group_system')
        is_cto = user.has_group('kg_timeoff_dashboard.group_admin_india_dashboard')

        companies = self.env['res.company'].search([])
        company_data = [{"id": company.id, "name": company.name} for company in companies]

        if is_cto:
            companies = self.env['res.company'].search([('id', '=', user.company_id.id)])
            company_data = [{"id": company.id, "name": company.name} for company in companies]

            current_company = user.company_id
            all_employees_vals = self.env['hr.employee'].sudo().search([
                ('exclude_in_dashboard', '=', False),
                ('company_id', '=', current_company.id)
            ])
            late_requests = self.env['early.late.request'].sudo().search([
                ('type', '=', 'late_arrival'),
                ('employee_id.company_id', '=', current_company.id)
            ])
        else:
            all_employees_vals = self.env['hr.employee'].sudo().search([
                ('exclude_in_dashboard', '=', False)
            ])
            late_requests = self.env['early.late.request'].sudo().search([
                ('type', '=', 'late_arrival')
            ])

        start_of_week = current_date - timedelta(days=current_date.weekday() + 1)
        if start_of_week > current_date:
            start_of_week -= timedelta(weeks=1)
        end_of_week = start_of_week + timedelta(days=6)

        employee_data = []
        all_employee_data = []

        for rec in all_employees_vals:
            all_employee_data.append({
                "id": rec.id,
                "name": rec.name,
            })

        def parse_time_string(time_str):
            """Parse 'X hours, Y minutes, Z seconds' OR old 'X hours and Y minutes'."""
            hours = minutes = seconds = 0
            if "," in time_str:
                parts = time_str.split(',')
                try:
                    hours = int(parts[0].split(' ')[0])
                    minutes = int(parts[1].split(' ')[1])
                    seconds = int(parts[2].split(' ')[1]) if len(parts) > 2 else 0
                except Exception:
                    pass
            else:
                match = re.match(r"(\d+) hours? and (\d+) minutes?", time_str)
                if match:
                    hours = int(match.group(1))
                    minutes = int(match.group(2))
            return hours, minutes, seconds

        for request in late_requests:
            employee = request.employee_id

            late_requests_month = self.env['early.late.request'].sudo().search([
                ('type', '=', 'late_arrival'),
                ('employee_id', '=', employee.id),
                ('date_late', '>=', start_of_month),
                ('date_late', '<=', end_of_month)
            ])
            late_week = self.env['early.late.request'].sudo().search([
                ('type', '=', 'late_arrival'),
                ('employee_id', '=', employee.id),
                ('date_late', '>=', start_of_week),
                ('date_late', '<=', end_of_week)
            ])

            time_strings_month = late_requests_month.mapped('late_hrs')
            time_strings_week = late_week.mapped('late_hrs')

            total_hours = total_minutes = total_seconds = 0
            for time_str in time_strings_month:
                hours, minutes, seconds = parse_time_string(time_str)
                total_hours += hours
                total_minutes += minutes
                total_seconds += seconds

            total_minutes += total_seconds // 60
            total_seconds = total_seconds % 60
            total_hours += total_minutes // 60
            total_minutes = total_minutes % 60

            hours_week = minutes_week = seconds_week = 0
            for time_str in time_strings_week:
                hours, minutes, seconds = parse_time_string(time_str)
                hours_week += hours
                minutes_week += minutes
                seconds_week += seconds

            minutes_week += seconds_week // 60
            seconds_week = seconds_week % 60
            hours_week += minutes_week // 60
            minutes_week = minutes_week % 60

            formatted_time = "00:00:00 Hrs"
            match = re.match(r"(\d+) hours?, (\d+) minutes?, (\d+) seconds?", request.late_hrs)
            if match:
                hours = int(match.group(1))
                minutes = int(match.group(2))
                seconds = int(match.group(3))
                formatted_time = f"{hours:02}:{minutes:02}:{seconds:02} Hrs"

            if request.type == 'late_arrival':
                employee_data.append({
                    "id": request.id,
                    "employee_id": employee.id,
                    "name": employee.name,
                    "company_id": employee.company_id.id,
                    "company_name": employee.company_id.name,
                    "date": request.date_late,
                    "late_by": formatted_time,
                    "arrival_time": request.time_string,
                    "week_late": f"{hours_week:02}:{minutes_week:02}:{seconds_week:02}",
                    "monthly_late": f"{total_hours:02}:{total_minutes:02}:{total_seconds:02}",
                    "late": {
                        "total_late": late_requests_month.ids,
                        "current_late": request.ids,
                        "week_late": late_week.ids
                    },
                })

        return {
            "current_company_id": user.company_id.id,
            "companies": company_data,
            "employees": employee_data,
            "all_employees": all_employee_data,
            "tree_view": self.env.ref('kg_attendance.early_late_request_tree').id
        }

    @api.model
    def get_employees_by_company(self, company_id=None):
        """
        Fetch all employees by company_id.
        If no company_id is provided, return all employees.
        """
        if company_id:
            employees = self.sudo().search([('company_id', '=', company_id), ('exclude_in_dashboard', '=', False)])
        else:
            employees = self.sudo().search([('exclude_in_dashboard', '=', False)])

        return [{
            'id': emp.id,
            'name': emp.name,
            'company_name': emp.company_id.name if emp.company_id else '',
        } for emp in employees]

    @api.model
    def get_values_to_approve(self):
        current_date = fields.Date.today()

        start_of_month = current_date.replace(day=1)
        end_of_month = (datetime(current_date.year, current_date.month, 1) + timedelta(days=32)).replace(
            day=1) - timedelta(days=1)

        user = self.env.user
        is_admin = user.has_group('base.group_system')
        is_cto = user.has_group('kg_timeoff_dashboard.group_admin_india_dashboard')

        companies = self.env['res.company'].search([])
        if is_cto:
            companies = self.env.company
        company_data = [{"id": company.id, "name": company.name} for company in companies]

        domain = [('state', 'not in', ('lm_approved', 'cancel', 'draft'))]
        if is_cto:
            domain.append(('company_name', '=', self.env.company.id))

        late_requests = self.env['early.late.request'].sudo().search(domain)

        all_employees_vals = self.env['hr.employee'].sudo().search([('exclude_in_dashboard', '=', False)])

        # Week boundaries (Sunday – Saturday)
        start_of_week = current_date - timedelta(days=current_date.weekday() + 1)
        if start_of_week > current_date:
            start_of_week -= timedelta(weeks=1)
        end_of_week = start_of_week + timedelta(days=6)

        employee_data = []
        employee_data_early = []
        all_employee_data = [{"id": rec.id, "name": rec.name} for rec in all_employees_vals]

        # ---------------------------
        # Helpers
        # ---------------------------
        def parse_time_string(time_str):
            hours = minutes = seconds = 0
            if not time_str:
                return 0, 0, 0
            try:
                if "," in time_str:  # New format
                    parts = [p.strip() for p in time_str.split(",")]
                    if len(parts) >= 1:
                        hours = int(parts[0].split()[0])
                    if len(parts) >= 2:
                        minutes = int(parts[1].split()[0])
                    if len(parts) >= 3:
                        seconds = int(parts[2].split()[0])
                else:  # Old format
                    match = re.match(r"(\d+)\s+hours?\s+and\s+(\d+)\s+minutes?", time_str)
                    if match:
                        hours = int(match.group(1))
                        minutes = int(match.group(2))
            except Exception:
                pass
            return hours, minutes, seconds

        def sum_times(time_strings):
            total_h = total_m = total_s = 0
            for ts in time_strings:
                h, m, s = parse_time_string(ts)
                total_h += h
                total_m += m
                total_s += s

            # Normalize
            total_m += total_s // 60
            total_s = total_s % 60
            total_h += total_m // 60
            total_m = total_m % 60

            return total_h, total_m, total_s

        for request in late_requests:
            employee = request.employee_id

            if request.type == 'late_arrival':
                request_time_str = request.late_hrs or ""
                date = request.date_late.strftime("%d/%m/%Y")

                late_requests_month = self.env['early.late.request'].sudo().search([
                    ('type', '=', 'late_arrival'),
                    ('employee_id', '=', employee.id),
                    ('date_late', '>=', start_of_month),
                    ('date_late', '<=', end_of_month)
                ])

                late_week = self.env['early.late.request'].sudo().search([
                    ('type', '=', 'late_arrival'),
                    ('employee_id', '=', employee.id),
                    ('date_late', '>=', start_of_week),
                    ('date_late', '<=', end_of_week)
                ])

                total_h, total_m, total_s = sum_times(late_requests_month.mapped('late_hrs'))
                week_h, week_m, week_s = sum_times(late_week.mapped('late_hrs'))

            elif request.type == 'early_departure':
                request_time_str = request.early_hrs or ""
                date = request.date_early.strftime("%d/%m/%Y")

                late_requests_month = self.env['early.late.request'].sudo().search([
                    ('type', '=', 'early_departure'),
                    ('employee_id', '=', employee.id),
                    ('date_early', '>=', start_of_month),
                    ('date_early', '<=', end_of_month)
                ])

                late_week = self.env['early.late.request'].sudo().search([
                    ('type', '=', 'early_departure'),
                    ('employee_id', '=', employee.id),
                    ('date_early', '>=', start_of_week),
                    ('date_early', '<=', end_of_week)
                ])

                total_h, total_m, total_s = sum_times(late_requests_month.mapped('early_hrs'))
                week_h, week_m, week_s = sum_times(late_week.mapped('early_hrs'))

            # Format display
            h, m, s = parse_time_string(request_time_str)
            formatted_time = f"{h:02}:{m:02}:{s:02} Hrs"

            values = {
                "id": request.id,
                "employee_id": employee.id,
                "name": employee.name,
                "company_id": employee.company_id.id,
                "company_name": employee.company_id.name,
                "date": date,
                "reason": request.reason,
                "late_by": formatted_time,
                "arrival_time": request.time_string,
                "week_late": f"{week_h:02}:{week_m:02}:{week_s:02}",
                "monthly_late": f"{total_h:02}:{total_m:02}:{total_s:02}",
                "late": {
                    "total_late": late_requests_month.ids,
                    "current_late": request.ids,
                    "week_late": late_week.ids
                },
            }

            if request.type == 'late_arrival':
                employee_data.append(values)
            elif request.type == 'early_departure':
                employee_data_early.append(values)

        return {
            "current_company_id": self.env.company.id,
            "companies": company_data,
            "employees": employee_data,
            "employees_early": employee_data_early,
            "all_employees": all_employee_data,
            "tree_view": self.env.ref('kg_attendance.early_late_request_tree').id
        }

class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    exclude_in_dashboard = fields.Boolean(string="Exclude from Dashboard")
    exclude_from_timesheet = fields.Boolean(string="Exclude from Timesheet")


