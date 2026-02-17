from datetime import date

from odoo import models, fields, api


class KgLeaveDashboard(models.Model):
    _inherit = 'hr.leave'

    def get_leave_details(self):
        today = date.today()
        current_year = date.today().year

        start_date = f"{current_year}-01-01"
        end_date = f"{current_year}-12-31"

        user = self.env.user
        is_admin = user.has_group('base.group_system')

        print("is_admin", is_admin)

        teams = self.env['project.team'].sudo().search([('timesheet_user_ids', '=', user.id)])
        print("teams:", teams)
        current_company = user.company_id
        domain = [
            ('date_from', '<=', today),
            ('date_to', '>=', today),
            ('state', '!=', 'refuse'),
        ]
        team_member_ids = []
        user_company_id = self.env.company.id
        is_cto = user.has_group('kg_timeoff_dashboard.group_admin_india_dashboard')

        if is_cto:
            team_member_ids = self.env['hr.employee'].sudo().search([
                ('company_id', '=', user.company_id.id)
            ]).ids
            domain.append(('employee_ids', 'in', team_member_ids))

        elif not is_admin and teams:
            user_ids = teams.mapped('employee_ids').ids
            print("team_member_ids:", teams.mapped('employee_ids'))
            team_member_ids = self.env['hr.employee'].sudo().search(
                [('user_id', 'in', user_ids), ('company_id', '=', user_company_id)]).ids

            domain.append(('employee_ids', 'in', team_member_ids))

        elif not is_admin and not teams and user.has_group('hr_holidays.group_hr_holidays_user'):
            # team_member_ids = self.env['hr.employee'].sudo().search([]).ids
            team_member_ids = self.env['hr.employee'].sudo().search([('company_id', '=', user_company_id)]).ids
            print("team_member_idsuuuu:", teams.mapped('employee_ids'))
            domain.append(('employee_ids', 'in', team_member_ids))
        elif not is_admin and not teams:
            print("2nd if")
            # user_ids = teams.mapped('employee_ids').ids
            team_member_ids = self.env['hr.employee'].sudo().search([('user_id', '=', user.id)]).ids

            domain.append(('employee_ids', 'in', team_member_ids))
        else:
            print("last if")

            team_member_ids = self.env['hr.employee'].sudo().search([]).ids
            # team_member_ids = self.env['hr.employee'].sudo().search([('company_id', '=', user_company_id)]).ids
            print("team_member_idsuuuu:", teams.mapped('employee_ids'))
            domain.append(('employee_ids', 'in', team_member_ids))
        # if current_company:
        #     domain.append(('company_id', '=', current_company.id))

        print("final_domain:", domain)

        leaves_today = self.env['hr.leave'].sudo().search(domain)

        leave_details = []

        for leave in leaves_today:
            employee = leave.employee_id
            joining_date = employee.date_joining or date(current_year, 1, 1)
            start_date = max(joining_date, date(current_year, 1, 1))
            end_date = date(current_year + 1, 12, 31)

            allocation_domain = [
                ('employee_id', '=', employee.id),
                '|', ('date_from', '>=', start_date),
                ('date_to', '<=', end_date),
                '|', ('date_to', '>=', today),
                ('date_to', '=', False),
            ]
            leave_domain = [
                ('employee_id', '=', employee.id),
                ('state', '=', 'validate'),
                ('date_from', '>=', start_date),
                ('date_to', '<=', end_date),

            ]

            sick_leave_type = self.env['hr.leave.type'].search([('time_off_type', '=', 'is_sick')])
            total_sick_leaves = sum(
                leave.number_of_days for leave in self.env['hr.leave'].sudo().search(
                    leave_domain + [('holiday_status_id', 'in', [sick_leave.id for sick_leave in sick_leave_type])]
                )
            )
            print("total sick", total_sick_leaves)

            sick_leave_allocation = self.env['hr.leave.allocation'].sudo().search(
                allocation_domain + [
                    ('holiday_status_id', 'in', [sick_leave.id for sick_leave in sick_leave_type])]
            )

            total_sick_allocation = sum(allocation.number_of_days for allocation in sick_leave_allocation)

            # Casual/Annual leave based on country
            if employee.company_id.country_code == 'IN':
                casual_leave_type = self.env['hr.leave.type'].search([('time_off_type', '=', 'is_casual')])
            else:
                casual_leave_type = self.env['hr.leave.type'].search([('time_off_type', '=', 'is_annual')])

            total_casual_leaves = sum(leave.number_of_days for leave in self.env['hr.leave'].search(
                leave_domain + [('holiday_status_id', 'in', [casual_leave.id for casual_leave in casual_leave_type])]
            ))
            print("total_casual_leaves", total_casual_leaves)

            casual_leave_allocation = self.env['hr.leave.allocation'].sudo().search(
                allocation_domain + [
                    ('holiday_status_id', 'in', [casual_leave.id for casual_leave in casual_leave_type])]
            )
            total_casual_allocation = sum(allocation.number_of_days for allocation in casual_leave_allocation)

            # Unpaid leave
            unpaid_leave_type = self.env['hr.leave.type'].search([('time_off_type', '=', 'is_unpaid')], limit=1)
            total_unpaid_leave = sum(leave.number_of_days for leave in self.env['hr.leave'].search(
                leave_domain + [('holiday_status_id', '=', unpaid_leave_type.id)]
            ))

            unpaid_leave_allocation = self.env['hr.leave.allocation'].search(
                allocation_domain + [('holiday_status_id', '=', unpaid_leave_type.id)]
            )
            total_unpaid_allocation = sum(allocation.number_of_days for allocation in unpaid_leave_allocation)

            # Total allocation (combined sick, casual/annual, and unpaid)
            total_allocation = sum(
                allocation.number_of_days for allocation in self.env['hr.leave.allocation'].search(
                    allocation_domain + [
                        ('holiday_status_id', 'in',
                         [sick_leave.id for sick_leave in sick_leave_type] + [casual_leave.id for casual_leave in
                                                                              casual_leave_type] + [
                             unpaid_leave_type.id])
                    ]
                )
            )
            print("Total allocation", total_allocation)
            total_allocated_leaves = total_sick_allocation + total_casual_allocation

            leave_details.append({
                'id': leave.id,
                'employee_name': employee.name,
                'employee_id': employee.id,
                'company_id': employee.company_id.name,
                'leave_type': leave.holiday_status_id.name,
                'duration': leave.number_of_days_display,
                'start_date': leave.date_from.date().strftime('%d/%m/%Y'),
                'end_date': leave.date_to.date().strftime('%d/%m/%Y'),
                'remaining_leaves': max(0, total_allocation - (total_casual_leaves + total_sick_leaves)),
                'total_allocated_leaves': total_allocated_leaves,
                'leaves': [leave.id for leave in leaves_today if leave.employee_id.id == employee.id],
                # Filter leave IDs for this employee
            })

        return leave_details
