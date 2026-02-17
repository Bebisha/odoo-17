from odoo import models, fields, _
from datetime import date


class ProjectTaskAnalysis(models.Model):
    _name = 'task.analysis'

    project_id = fields.Many2one('project.project', string="Project")
    team_id = fields.Many2one('project.team')
    assignee_id = fields.Many2one('res.users', string="Assignee")
    today_count = fields.Integer(string='Today')
    hold_count = fields.Integer(string='Held')
    pending_total = fields.Integer(string='Pending Total')
    fixed_count = fields.Integer(string='Fixed')
    inbox_count = fields.Integer(string='Open')
    over_due = fields.Integer(string='Over Due')
    total = fields.Integer(string='Total')

    # def load_task_details(self):
    #     self.env.cr.execute("""select
    #             row_number() over(ORDER BY min(t.id)) as id,
    #             min(t.id) as timeline_line_id,
    #             k.name as project_id,
    #             t.milestone_id as milestone_id,
    #                                 min(t.line_start_date) as line_start_date,
    #                                 max(t.line_end_date) as line_end_date
    #
    #             from timeline_line t
    #             left join kg_project_timeline k on k.id=t.project_id
    #             group by t.milestone_id, k.name;""")
    #     res = self.env.cr.fetchone()
    #     teams = self.env['project.team'].search([])
    #     domain_list = []
    #     today = date.today()
    #     for team in teams:
    #         for emp in team.employee_ids:
    #             emp_tasks = self.env['project.task'].search(
    #                 [('user_ids', '=', emp.id), ('stage_id.is_closed', '!=', True)])
    #             projects = list(set(emp_tasks.mapped('project_id')))
    #             for proj in projects:
    #                 proj_tasks = emp_tasks.filtered(lambda x: x.project_id == proj)
    #                 open_task_count = len(proj_tasks.filtered(lambda x: x.date_deadline > today and not x.stage_id.is_hold and not x.stage_id.is_fixed and not x.stage_id.is_closed))
    #                 fixed_task_count = len(proj_tasks.filtered(lambda x: x.stage_id.is_fixed))
    #                 today_task_count = len(proj_tasks.filtered(lambda x: x.date_deadline == today and not x.stage_id.is_hold and not x.stage_id.is_fixed and not x.stage_id.is_closed))
    #                 overdue_task_count = len(proj_tasks.filtered(lambda x: x.date_deadline < today and not x.stage_id.is_hold and not x.stage_id.is_fixed and not x.stage_id.is_closed))
    #                 hold_task_count = len(proj_tasks.filtered(lambda x: x.stage_id.is_hold))
    #                 pending_total = open_task_count + today_task_count + overdue_task_count
    #                 total = open_task_count + today_task_count + overdue_task_count + hold_task_count + fixed_task_count
    #                 record = self.env['task.analysis'].create(
    #                     {'assignee_id': emp.id, 'team_id': team.id, 'project_id': proj.id,
    #                      'inbox_count': open_task_count, 'today_count': today_task_count,
    #                      'fixed_count': fixed_task_count, 'over_due': overdue_task_count,
    #                      'hold_count': hold_task_count, 'total': total,'pending_total':pending_total})
    #                 domain_list.append(record.id)
    #             if not emp_tasks:
    #                 record = self.env['task.analysis'].create(
    #                     {'assignee_id': emp.id, 'team_id': team.id, 'project_id': False,
    #                      'inbox_count': 0, 'today_count': 0, 'fixed_count': 0, 'over_due': 0,
    #                      'hold_count': 0, 'total': 0,'pending_total':0})
    #                 domain_list.append(record.id)
    #     return {
    #         'name': _('Task Report'),
    #         'view_type': 'form',
    #         'view_mode': 'pivot,tree',
    #         'domain': [('id', 'in', domain_list)],
    #         'context': {'search_default_groupby_team': 1, 'search_default_groupby_assignee': 1, 'search_default_groupby_project': 1},
    #         'res_model': 'task.analysis',
    #         'type': 'ir.actions.act_window',
    #         'target': 'main'
    #     }
