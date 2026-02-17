from datetime import date

from odoo import http
from odoo.http import request, _logger

from odoo import http
from odoo.http import request


class TimeOffDashboardController(http.Controller):
    @http.route('/timeoff/sick_leave', type='http', auth="user", website=True)
    def view_employee_sick_leave(self, employee_id=None, leave_type_id=None):
        current_year = date.today().year
        start_date = f"{current_year}-01-01"
        end_date = f"{current_year}-12-31"

        if employee_id:
            employee = request.env['hr.employee'].sudo().browse(int(employee_id))
            holiday_status_id = request.env['hr.leave.type'].sudo().search(
                [('time_off_type', '=', 'is_sick')], limit=1
            )

            leave_records = request.env['hr.leave'].sudo().search([
                ('employee_id', '=', int(employee_id)),
                ('state', '=', 'validate'),
                ('holiday_status_id', '=', holiday_status_id.id),
                ('date_from', '>=', start_date),
                ('date_to', '<=', end_date),
            ])
            leave_records.write({'is_go_back': True})

            action = request.env.ref('kg_timeoff_dashboard.action_employee_sick_leave_tree')
            domain = [
                ('employee_id', '=', int(employee_id)),
                ('state', '=', 'validate'),
                ('holiday_status_id', '=', holiday_status_id.id),
                ('date_from', '>=', start_date),
                ('date_to', '<=', end_date),
            ]
            action['domain'] = domain

            return request.render('kg_timeoff_dashboard.employee_casual_leave_template', {
                'employee': employee,
                'leave_records': leave_records,
            })

    @http.route('/timeoff/casual_leave', type='http', auth="user", website=True)
    def view_employee_casual_leave(self, employee_id=None, leave_type_id=None):
        current_year = date.today().year
        start_date = f"{current_year}-01-01"
        end_date = f"{current_year}-12-31"

        if employee_id:
            employee = request.env['hr.employee'].sudo().browse(int(employee_id))
            leave_type = 'is_casual' if employee.company_id.country_code == 'IN' else 'is_annual'

            holiday_status_id = request.env['hr.leave.type'].sudo().search(
                [('time_off_type', '=', leave_type)], limit=1
            )

            leave_records = request.env['hr.leave'].sudo().search([
                ('employee_id', '=', int(employee_id)),
                ('state', '=', 'validate'),
                ('holiday_status_id', '=', holiday_status_id.id),
                ('date_from', '>=', start_date),
                ('date_to', '<=', end_date),
            ])
            leave_records.write({'is_go_back': True})  # Update the records

            action = request.env.ref('kg_timeoff_dashboard.action_employee_sick_leave_tree')
            domain = [
                ('employee_id', '=', int(employee_id)),
                ('state', '=', 'validate'),
                ('holiday_status_id', '=', holiday_status_id.id),
                ('date_from', '>=', start_date),
                ('date_to', '<=', end_date),
            ]
            action['domain'] = domain

            return request.render('kg_timeoff_dashboard.employee_casual_leave_template', {
                'employee': employee,
                'leave_records': leave_records,
            })

    @http.route('/timeoff/unpaid', type='http', auth="user", website=True)
    def view_employee_unpaid_leave(self, employee_id=None, leave_type_id=None):
        current_year = date.today().year
        start_date = f"{current_year}-01-01"
        end_date = f"{current_year}-12-31"

        if employee_id:
            employee = request.env['hr.employee'].sudo().browse(int(employee_id))
            holiday_status_id = request.env['hr.leave.type'].sudo().search(
                [('time_off_type', '=', 'is_unpaid')],
                limit=1
            )

            leave_records = request.env['hr.leave'].sudo().search([
                ('employee_id', '=', int(employee_id)),
                ('state', '=', 'validate'),
                ('holiday_status_id', '=', holiday_status_id.id),
                ('date_from', '>=', start_date),
                ('date_to', '<=', end_date),
            ])
            leave_records.write({'is_go_back': True})

            action = request.env.ref('kg_timeoff_dashboard.action_employee_sick_leave_tree')
            domain = [
                ('employee_id', '=', int(employee_id)),
                ('state', '=', 'validate'),
                ('holiday_status_id', '=', holiday_status_id.id),
                ('date_from', '>=', start_date),
                ('date_to', '<=', end_date),
            ]
            action['domain'] = domain

            return request.render('kg_timeoff_dashboard.employee_casual_leave_template', {
                'employee': employee,
                'leave_records': leave_records,
            })
