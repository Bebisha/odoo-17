import json
import requests

from odoo.addons.portal.controllers.portal import CustomerPortal, pager
from odoo import http
from odoo.http import request, _logger


class PortalTimeSheet(CustomerPortal):

    @http.route('/employee/timesheet_form', type='http', auth='user', website=True)
    def timesheet_form(self, **kwargs):
        # client_ip = request.httprequest.remote_addr
        # _logger.info(f"Client IP: {client_ip}")
        #
        # url = f"https://ipinfo.io/{client_ip}/json"
        # response = requests.get(url)
        # data = response.json()
        # _logger.info(f"IP Info Data: {data}")
        #
        # # Extract country from the response
        # country = data.get('country', 'Unknown')
        # _logger.info(f"Client Country: {country}")
        # allowed_countries = ['ZA', 'NG', 'KE', 'EG', 'GH', 'MA']  # Add more country codes as needed
        # if country not in allowed_countries:
        #     print("fggggggggggggggggggg")
        #     return request.redirect('/web/login')
        user = request.env.user
        manager_employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
        if manager_employee:
            employees = request.env['hr.employee'].sudo().search([('coach_id', '=', manager_employee.id)])
        else:
            employees = request.env['hr.employee'].sudo().browse()
        projects = request.env['project.project'].sudo().search([('user_id', '=', user.id)])
        if employees:
            emp = request.env['res.users'].sudo().search([('employee_id', 'in', employees.ids)])
        if projects:
            project_ids = projects.ids
            tasks = request.env['project.task'].sudo().search(
                [('project_id', 'in', project_ids), ('user_ids', '=', user.id)])
        else:
            tasks = request.env[
                'project.task'].sudo().search([])
        values = {'employees': employees,
                  'employee_id': user.id if user else '',
                  'projects': projects,
                  'tasks': tasks, }
        return request.render('kg_portal_hrms.portal_timesheet_form', values)

    # @http.route(['/employee/get_project'], type='json', methods=["POST"], auth='public')
    # def get_user_id_project(self, **kw):
    #     data = json.loads(request.httprequest.data)
    #     projectId = data.get('projectId')
    #     if userId:
    #         tasks = request.env['project.task'].sudo().search([('user_ids', '=', userId)])
    #         project_ids = tasks.mapped('project_id')
    #         project_data = [{'id': proj.id, 'name': proj.name} for proj in project_ids]
    #         task_data = [{'id': task.id, 'name': task.name, 'project_id': task.project_id.id} for task in tasks]
    #         return {
    #             'projects': project_data,
    #             'tasks': task_data
    #         }
    #
    #
    #     return {'projects': [], 'tasks': []}

    @http.route(['/employee/get_projects'], type='json', methods=["POST"], auth='public')
    def get_project(self, **kw):
        data = json.loads(request.httprequest.data)
        employeeId = data.get('employeeId')
        if employeeId:
            userId = request.env['hr.employee'].sudo().browse(int(employeeId)).user_id
            tasks = request.env['project.task'].sudo().search([('user_ids', '=', userId.ids)])
            project_ids = tasks.mapped('project_id')
            project_data = [{'id': proj.id, 'name': proj.name} for proj in project_ids]
            task_data = [{'id': task.id, 'name': task.name, 'project_id': task.project_id.id} for task in tasks]
            return {
                'projects': project_data,
                'tasks': task_data
            }

        return {'projects': [], 'tasks': []}

    @http.route('/employee/timesheet_form/submit', type='http', auth='user', methods=['POST'], website=True, csrf=False)
    def submit_timesheet_form(self, **post):
        hours_str = post.get('hours', '0:00')
        hours, minutes = map(int, hours_str.split(':'))
        total_hours = hours + minutes / 60.0
        employee_id = post.get('employee_id')
        project_id = post.get('project_id')
        task_id = post.get('task_id')
        date = post.get('date')
        employees = post.get('employees_id')
        description = post.get('description')
        user = request.env.user
        if employees:
            timesheet = request.env['account.analytic.line'].sudo().search([
                ('project_id', '=', project_id),
                ('task_id', '=', task_id),
                ('employee_id', '=', int(employees)),
                ('date', '=', date)
            ], limit=1)
            task = request.env['project.task'].sudo().search([('id', '=', task_id)], limit=1)
            if timesheet:
                timesheet.sudo().write({
                    'hours': total_hours,
                    'description': description
                })
                if task:
                    task.message_post(body=f'Timesheet updated: {date} date recorded by {user.name}.')
                else:
                    _logger.warning(f'Task with ID {task_id} not found.')
            else:

                new_timesheet = request.env['account.analytic.line'].sudo().create({
                    'employee_id': int(employees),
                    'date': date,
                    'unit_amount': total_hours,
                    'project_id': int(project_id),
                    'task_id': int(task_id),
                    'name': description,
                })

                if task:  # Ensure the task is found
                    task.message_post(body=f'Timesheet created: {date} date recorded by {user.name}.')
                else:
                    _logger.warning(f'Task with ID {task_id} not found.')
        else:
            emp = request.env['hr.employee'].search([('user_id','=',user.id)])

            timesheet = request.env['account.analytic.line'].sudo().search([
                ('project_id', '=', project_id),
                ('task_id', '=', task_id),
                ('user_id', '=', user.id),
                ('employee_id', '=', emp.id),
                ('date', '=', date)
            ], limit=1)
            task = request.env['project.task'].sudo().search([('id', '=', task_id)], limit=1)
            if timesheet:
                timesheet.sudo().write({
                    'hours': total_hours,
                    'description': description
                })
                if task:  # Ensure the task is found
                    task.message_post(body=f'Timesheet updated: {date} date recorded by {user.name}.')
                else:
                    _logger.warning(f'Task with ID {task_id} not found.')

            else:
                new_timesheet = request.env['account.analytic.line'].sudo().create({
                    'employee_id': emp.id,
                    'date': date,
                    'unit_amount': total_hours,
                    'project_id': int(project_id),
                    'task_id': int(task_id),
                    'name': description,
                })

                if task:  # Ensure the task is found
                    task.message_post(body=f'Timesheet created: {date} date recorded by {user.name}.')
                else:
                    # Handle case where task is not found (optional)
                    _logger.warning(f'Task with ID {task_id} not found.')

        # Redirect to a thank you page after submission
        return request.redirect('/portal/timesheet_form/thank_you')

    @http.route('/portal/timesheet_form/thank_you', type='http', auth='user', website=True)
    def thank_you_timesheet(self, **kwargs):
        return request.render('kg_portal_hrms.thank_you_page')

