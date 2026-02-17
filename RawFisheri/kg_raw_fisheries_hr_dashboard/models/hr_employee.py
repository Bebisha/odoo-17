# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def get_employee_data(self, status_filter='active'):
        """ Function to load data for the dashboard """

        domain = [('sponsor_name', '!=', False)]

        if status_filter == 'active':
            domain.append(('employee_status', '=', 'active'))
        elif status_filter == 'inactive':
            domain.append(('employee_status', '=', 'not_active'))

        employees = self.env['hr.employee'].search(domain)
        vessels_by_department = {}
        for employee in employees:
            vessel_id = employee.sponsor_name.id
            department_id = employee.department_id.id
            vessel_name = employee.sponsor_name.name or 'Unknown'
            department_name = employee.department_id.name or 'Unknown'

            if vessel_id not in vessels_by_department:
                vessels_by_department[vessel_id] = {
                    'vessel': vessel_name,
                    'departments': {}
                }

            if department_id not in vessels_by_department[vessel_id]['departments']:
                vessels_by_department[vessel_id]['departments'][department_id] = {
                    'department': department_name,
                    'employees': [],
                    'total_salary': 0.0,
                    'employee_count': 0
                }

            employee_data = {
                'name': employee.name,
                'id': employee.id,
                'job_title': employee.job_id.name,
                'date_start': employee.contract_id.date_start,
                'date_end': employee.contract_id.date_end,
                'salary': employee.contract_id.wage or 0.0,
            }
            vessels_by_department[vessel_id]['departments'][department_id]['employees'].append(employee_data)
            vessels_by_department[vessel_id]['departments'][department_id][
                'total_salary'] += employee.contract_id.wage or 0.0
            vessels_by_department[vessel_id]['departments'][department_id]['employee_count'] += 1

        result = []
        for vessel_data in vessels_by_department.values():
            departments_list = []
            for department_data in vessel_data['departments'].values():
                departments_list.append({
                    'department': department_data['department'],
                    'employees': department_data['employees'],
                    'total_salary': department_data['total_salary'],
                    'employee_count': department_data['employee_count'],
                })
            result.append({
                'vessel': vessel_data['vessel'],
                'departments': departments_list,
            })
        return {
            'vessels_by_department': result,
        }
