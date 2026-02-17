from odoo import http
from odoo.http import request
from datetime import date, datetime
import logging

_logger = logging.getLogger(__name__)


class EmployeeDashboardController(http.Controller):

    @http.route('/employee_dashboard/employees', auth='user', type='json')
    def get_managed_employees(self):
        user = request.env.user
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
        if not employee:
            return {}

        managed_emps = request.env['hr.employee'].sudo().search([('parent_id', '=', employee.id)])

        project_map = {}
        unassigned_employees = []
        forecasted_employees = []
        today = date.today()

        assigned_employees = []

        for emp in managed_emps:
            _logger.info("Processing employee: %s", emp.name)
            if emp.user_id:
                tasks = request.env['project.task'].sudo().search([('user_ids', 'in', emp.user_id.id)])
                _logger.info("Tasks found for %s: %s", emp.name, [task.name for task in tasks])

                assigned_tasks = []
                forecasted_tasks = []
                project_ids = set()

                latest_deadline = None


                for task in tasks:
                    start_date = task.planned_date_begin
                    if isinstance(start_date, datetime):
                        start_date = start_date.date()
                    task_data = {'id': task.id, 'name': task.name}

                    if task.project_id:
                        project_ids.add(task.project_id.id)

                    if task.date_deadline:
                        if not latest_deadline or task.date_deadline > latest_deadline:
                            latest_deadline = task.date_deadline

                    if start_date:
                        if start_date <= today:
                            assigned_tasks.append(task_data)
                        else:
                            forecasted_tasks.append(task_data)
                    else:
                        assigned_tasks.append(task_data)

                if assigned_tasks:
                    assigned_employees.append({
                        'name': emp.name,
                        'tasks': assigned_tasks,
                        'project_ids': list(project_ids),
                        'latest_deadline': latest_deadline.strftime('%d/%m/%Y') if latest_deadline else '',

                    })
                elif not forecasted_tasks:
                    unassigned_employees.append({
                        'name': emp.name,
                        'tasks': [],
                        'project_ids': list(project_ids),
                        'latest_deadline': '',

                    })

                if forecasted_tasks:
                    forecasted_employees.append({
                        'name': emp.name,
                        'tasks': forecasted_tasks,
                        'project_ids': list(project_ids),

                    })

            else:
                unassigned_employees.append({
                    'name': emp.name,
                    'tasks': [],
                    'project_ids': [],
                    'latest_deadline': '',

                })

        return {
            'assigned': assigned_employees,
            'unassigned': unassigned_employees,
            'forecasted': forecasted_employees,
        }
