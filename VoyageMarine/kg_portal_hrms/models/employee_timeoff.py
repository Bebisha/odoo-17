from odoo import models, fields, api


class TimeOff(models.Model):
    _name = 'employee.time_off'
    _description = 'Time Off Request'

    employee_id = fields.Char(string='Employee ID', required=True)
    holiday_status_id = fields.Char(string='Time Off Type', required=True)
    number_of_days_display = fields.Char(string='Duration', required=True)
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    reason = fields.Text(string='Description', required=True)




class Employee(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def fetch_projects_and_tasks(self, employee_id):
        employee = self.browse(employee_id)


        projects = self.env['project.project'].search([('employee_ids', 'in', employee.id)])

        tasks = self.env['project.task'].search([('project_id', 'in', projects.ids)])

        project_data = [{'id': project.id, 'name': project.name} for project in projects]
        task_data = [{'id': task.id, 'name': task.name, 'project_id': task.project_id.id} for task in tasks]

        return {'projects': project_data, 'tasks': task_data}
