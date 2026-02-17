# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import date, datetime, timedelta

from odoo import tools
from odoo import api, fields, models


class ProjectStatusReport(models.AbstractModel):
    _name = 'report.kg_project_status_mail.report_project_details'

    _description = 'Project-Task Status  Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = []
        non_task = []
        docs = self.env['project.status.config'].browse(docids)
        active = []
        for i in docs:
            for rec in i.project_ids.filtered(lambda x: x.stage_id.is_closed != True):
                milestone = self.env['project.milestone'].search([
                    ('project_id', '=', rec.id),
                    ('is_reached', '!=', True)
                ], limit=1)
                status = {
                    'project_name': rec.name,
                    'status': rec.stage_id.name,
                    'milestone': milestone.name
                }
                active.append(status)

            for pro in i.project_ids:
                total_list = []
                project = {
                    'project': pro.name
                }
                task_id = self.env['project.task'].search(
                    [('project_id', 'in', pro.ids), ('stage_id.is_closed', '!=', True)])
                total_task_id = self.env['project.task'].search(
                    [('project_id', 'in', pro.ids),
                     ('date_deadline', '>=', date.today()), ('stage_id.is_closed', '!=', True)])
                overdue_task_id = self.env['project.task'].search(
                    [('project_id', 'in', pro.ids),
                     ('date_deadline', '<', date.today()), ('stage_id.is_closed', '!=', True)])
                assignees = task_id.mapped('user_ids')
                assignees_list = []
                project.update({'assignees_list': False})

                for ass in assignees:
                    total_task = total_task_id.filtered(lambda l: l.user_ids in ass)
                    over_due = overdue_task_id.filtered(lambda l: l.user_ids in ass)
                    if len(total_task) > 0 or len(over_due) > 0:
                        assignees_dict = {
                            'assignees': ass.name,
                            'total_task': len(total_task),
                            'over_due': len(over_due),
                        }
                        assignees_list.append(assignees_dict)
                        project.update({'assignees_list': assignees_list})
                total_dict = {
                    'sum_of_task': len(total_task_id),
                    'sum_of_overdue': len(overdue_task_id)
                }
                total_list.append(total_dict)
                project.update({'total_list': total_list})
                data.append(project)

                non_ass_task = self.env['project.task'].search(
                    [('user_ids', '=', False), ('project_id', 'in', pro.ids), ('stage_id.is_closed', '!=', True)])
                if non_ass_task:
                    non_task_vals = {
                        'project_name': pro,
                        'non_task': len(non_ass_task)
                    }
                    non_task.append(non_task_vals)

            return {
                'doc_ids': docs.ids,
                'doc_model': 'project.status.config',
                'docs': docs,
                'active': active,
                'data': data,
                'today': date.today(),
                'non_ass_data': non_task,

            }