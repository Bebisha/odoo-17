# -- coding: utf-8 --

import calendar
import random
from datetime import datetime, date

from dateutil.relativedelta import relativedelta

from odoo import models, api


class ProjectProject(models.Model):
    _inherit = 'project.project'

    # @api.model
    def get_project_data(self):
        task_tree = self.env.ref('kg_timeoff_dashboard.view_project_task_details_tree')
        user = self.env.user
        is_admin = user.has_group('base.group_system')
        task_ids = self.env['project.task'].search([])

        teams = self.env['project.team'].search([('timesheet_user_ids', '=', user.id)])
        domain = []
        user_ids = self.env['res.users']  # Initialize as an empty recordset
        # companies = self.env['res.company'].search([])
        companies = self.env.user.company_ids
        company_data = [{"id": company.id, "name": company.name} for company in companies]

        is_cto = user.has_group('kg_timeoff_dashboard.group_admin_india_dashboard')

        if is_cto:
            employees = self.env['hr.employee'].sudo().search([
                ('exclude_in_dashboard', '=', False),
                ('company_id', 'in', companies.ids)
            ])
            user_ids = employees.mapped('user_id')
            domain.append(('user_ids', 'in', user_ids.ids))

        elif not is_admin and teams:
            user_ids = teams.mapped('employee_ids')
            print("user_ids", user_ids)
            domain.append(('user_ids', 'in', user_ids.ids))
        elif not is_admin and not teams:
            # Only include the current user if they have an employee record
            employee = self.env['hr.employee'].search([('user_id', '=', user.id), ('exclude_in_dashboard', '=', False)],
                                                      limit=1)
            if employee:
                user_ids = self.env['res.users'].browse(user.id)  # Convert user to recordset
            domain.append(('user_ids', '=', user.id))
        else:
            # Get all users with an employee record
            all_users = self.env['res.users'].sudo().search([])
            for usr in all_users:
                # Check if user has an associated employee record
                employee = self.env['hr.employee'].sudo().search(
                    [('user_id', '=', usr.id), ('exclude_in_dashboard', '=', False)], limit=1)
                if employee:
                    user_ids |= usr  # Add user to the recordset
            domain.append(('user_ids', 'in', user_ids.ids))

        # if not is_admin and teams:
        #     user_ids = teams.mapped('employee_ids')
        #     domain.append(('user_ids','in',user_ids.ids))
        # elif not is_admin and not teams:
        #     user_ids = user
        #     domain.append(('user_ids','=',user.id))
        # else:
        #     user_ids = self.env['project.task'].search([('company_id','in',self.env.companies.ids)]).mapped('user_ids').sorted('name')
        #     # user_ids = self.env['res.users'].sudo().search([] )
        #     domain.append(('user_ids','=',user_ids.ids))
        # user_ids= user_ids.filtered(lambda x:x.company_id in self.env.companies)

        # domain = [
        #
        #     ('project_id', '!=', False),
        #     # ('user_ids', 'in', [user.id]),
        #     ('project_id.project_team_id.timesheet_user_ids', 'in', [user.id])
        # ]
        # task_ids = self.env['project.task'].search(domain)
        # task_ids = self.env['project.task'].search([])
        today = date.today()
        vals = []
        overdue_vals = []
        assignee_list = []
        no_task_vals = []
        for users in user_ids:
            # for tasks in task_ids:
            #     for emp in tasks.user_ids:
            if users not in assignee_list:
                assignee_list.append(users)
                #
                employee = {'id': users.id, 'name': users.name, 'company': users.company_id.name,
                            'company_id': users.company_id.id,
                            'open': 0, 'today': 0, 'overdue': 0, 'pending': 0, 'fixed': 0, 'held': 0,
                            'total': 0, 'task_ids': [], 'task_tree_id': task_tree.id, }
                vals.append(employee)
                overdue_vals.append({'id': users.id, 'name': users.name, 'company': users.company_id.name,
                                     'company_id': users.company_id.id, 'overdue': 0, 'task_ids': []})
        for assignee in assignee_list:
            emp_tasks = self.env['project.task'].sudo().search(
                [('user_ids', '=', assignee.id),
                 ('stage_id.is_closed', '!=', True)
                 ])

            open_task_count = len(emp_tasks.filtered(
                lambda x: isinstance(x.date_deadline, date) and
                          x.date_deadline > today and
                          not x.stage_id.is_hold and
                          not x.stage_id.is_fixed and
                          not x.stage_id.is_closed))

            open_task_ids = emp_tasks.filtered(
                lambda x: isinstance(x.date_deadline, date) and
                          x.date_deadline > today and
                          not x.stage_id.is_hold and
                          not x.stage_id.is_fixed and
                          not x.stage_id.is_closed)

            fixed_task_count = len(emp_tasks.filtered(lambda x: x.stage_id.is_fixed))
            fixed_task_ids = emp_tasks.filtered(lambda x: x.stage_id.is_fixed)
            today_task_count = len(emp_tasks.filtered(
                lambda x: isinstance(x.date_deadline, date) and
                          x.date_deadline == today and
                          not x.stage_id.is_hold and
                          not x.stage_id.is_fixed and
                          not x.stage_id.is_closed))

            today_task_ids = emp_tasks.filtered(
                lambda x: isinstance(x.date_deadline, date) and
                          x.date_deadline == today and
                          not x.stage_id.is_hold and
                          not x.stage_id.is_fixed and
                          not x.stage_id.is_closed)

            overdue_task_count = len(emp_tasks.filtered(
                lambda x: isinstance(x.date_deadline, date) and
                          x.date_deadline < today and
                          not x.stage_id.is_hold and
                          not x.stage_id.is_fixed and
                          not x.stage_id.is_closed))

            overdue_task_ids = emp_tasks.filtered(
                lambda x: isinstance(x.date_deadline, date) and
                          x.date_deadline < today and
                          not x.stage_id.is_hold and
                          not x.stage_id.is_fixed and
                          not x.stage_id.is_closed)
            hold_task_count = len(emp_tasks.filtered(lambda x: x.stage_id.is_hold))
            held_task_ids = emp_tasks.filtered(lambda x: x.stage_id.is_hold)
            pending_total = open_task_count + today_task_count + overdue_task_count
            pending_task_ids = open_task_ids + today_task_ids + overdue_task_ids
            total = open_task_count + today_task_count + overdue_task_count + hold_task_count + fixed_task_count
            total_task_ids = pending_task_ids + held_task_ids + fixed_task_ids
            if today_task_count == 0:
                no_task_vals.append({
                    'id': assignee.id,  # Add this line
                    'name': assignee.name,
                    'company': assignee.company_id.name,
                    'company_id': assignee.company_id.id
                })
            for item in vals:
                if item.get('id') == assignee.id:
                    item['open'] = open_task_count
                    item['today'] = today_task_count
                    item['overdue'] = overdue_task_count
                    item['pending'] = pending_total
                    item['fixed'] = fixed_task_count
                    item['held'] = hold_task_count
                    item['total'] = total
                    item['task_ids'] = {
                        'open': open_task_ids.ids,
                        'today': today_task_ids.ids,
                        'overdue': overdue_task_ids.ids,
                        'pending': pending_task_ids.ids,
                        'fixed': fixed_task_ids.ids,
                        'held': held_task_ids.ids,
                        'total': total_task_ids.ids,
                    }
            for i in range(len(overdue_vals) - 1, -1, -1):
                item = overdue_vals[i]
                if item.get('id') == assignee.id:
                    item['overdue'] = overdue_task_count
                    item['task_ids'] = {'overdue': overdue_task_ids.ids}

                    # If overdue_task_count is 0, remove the item
                    if overdue_task_count == 0:
                        del overdue_vals[i]

        max_length = max(len(no_task_vals), len(overdue_vals))
        range_list = list(range(1, max_length + 1))
        overdue_row_to_display = list(range(1, (max_length - len(overdue_vals)) + 1))
        no_task_row_to_display = list(range(1, (max_length - len(no_task_vals)) + 1))

        return {'summary': vals,
                'overdue': overdue_vals,
                'no_task': no_task_vals,
                'max_length': max_length,
                'range_list': range_list,
                'overdue_row_to_display': overdue_row_to_display,
                'no_task_row_to_display': no_task_row_to_display,
                "companies": company_data,
                "is_admin": is_admin
                }