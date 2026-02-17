# -*- coding: utf-8 -*-

import calendar
import random
from datetime import datetime, date

from dateutil.relativedelta import relativedelta

from odoo import models, api


class ProjectProject(models.Model):
    _inherit = 'project.project'

    @api.model
    def get_project(self):
        task_tree = self.env.ref('kg_dashboard_odoo.view_project_task_details_tree')
        task_ids = self.env['project.task'].search([])
        today = date.today()
        vals = []
        assignee_list = []
        for tasks in task_ids:
            for emp in tasks.user_ids:
                if emp not in assignee_list:
                    assignee_list.append(emp)
                    employee = {'id': emp.id, 'name': emp.name,
                                'open': 0, 'today': 0, 'overdue': 0, 'pending': 0, 'fixed': 0, 'held': 0,
                                'total': 0, 'task_ids': [],'task_tree_id': task_tree.id, }
                    vals.append(employee)
        for assignee in assignee_list:
            emp_tasks = self.env['project.task'].search(
                [('user_ids', '=', assignee.id),
                 ('stage_id.is_closed', '!=', True)
                 ])
            open_task_count = len(emp_tasks.filtered(lambda
                                                         x: x.date_deadline > today and not x.stage_id.is_hold and not x.stage_id.is_fixed and not x.stage_id.is_closed))
            open_task_ids = emp_tasks.filtered(lambda
                                                   x: x.date_deadline > today and not x.stage_id.is_hold and not x.stage_id.is_fixed and not x.stage_id.is_closed)
            fixed_task_count = len(emp_tasks.filtered(lambda x: x.stage_id.is_fixed))
            fixed_task_ids = emp_tasks.filtered(lambda x: x.stage_id.is_fixed)
            today_task_count = len(emp_tasks.filtered(lambda
                                                          x: x.date_deadline == today and not x.stage_id.is_hold and not x.stage_id.is_fixed and not x.stage_id.is_closed))
            today_task_ids = emp_tasks.filtered(lambda
                                                          x: x.date_deadline == today and not x.stage_id.is_hold and not x.stage_id.is_fixed and not x.stage_id.is_closed)
            overdue_task_count = len(emp_tasks.filtered(lambda
                                                            x: x.date_deadline < today and not x.stage_id.is_hold and not x.stage_id.is_fixed and not x.stage_id.is_closed))
            overdue_task_ids = emp_tasks.filtered(lambda
                                                            x: x.date_deadline < today and not x.stage_id.is_hold and not x.stage_id.is_fixed and not x.stage_id.is_closed)
            hold_task_count = len(emp_tasks.filtered(lambda x: x.stage_id.is_hold))
            held_task_ids = emp_tasks.filtered(lambda x: x.stage_id.is_hold)
            pending_total = open_task_count + today_task_count + overdue_task_count
            pending_task_ids = open_task_ids + today_task_ids + overdue_task_ids
            total = open_task_count + today_task_count + overdue_task_count + hold_task_count + fixed_task_count
            total_task_ids = pending_task_ids +  held_task_ids + fixed_task_ids
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

        return vals
