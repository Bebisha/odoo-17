from odoo import api, models, fields, _, Command
from datetime import date

from odoo.exceptions import ValidationError


class KGProjectProjectInherit(models.Model):
    _inherit = 'project.project'

    is_resource_pool_project = fields.Boolean(default=False, string="Is Resource Pool")
    is_engagement_project = fields.Boolean(default=False, string="Is Engagement Project")

class DailytaskAssign(models.Model):
    _name = 'daily.task.assign'
    _rec_name = 'assignee_id'

    @api.model
    def get_default_user(self):
        user_id = self.env.user.id
        if self.env['project.team'].search([('is_odoo', '=', True), ('employee_ids', 'in', user_id)], limit=1) or \
                self.env['project.team'].search([('is_resource_pool', '=', True), ('employee_ids', 'in', user_id)],
                                                limit=1):
            return user_id
        elif self.env['project.team'].search(
                [('is_odoo', '=', False), ('is_resource_pool', '=', False), ('employee_ids', 'in', user_id)], limit=1):
            return user_id
        return False

    @api.model
    def get_default_team(self):
        domain = [
            '|',
            ('is_odoo', '=', True),
            ('is_resource_pool', '=', True),
            ('employee_ids', 'in', self.env.user.id)
        ]
        team = self.env['project.team'].search(domain, limit=1)

        if not team:
            domain = [
                ('is_odoo', '=', False),
                ('is_resource_pool', '=', False),
                ('employee_ids', 'in', self.env.user.id)
            ]
            team = self.env['project.team'].search(domain, limit=1)

        return team or False


    team_id = fields.Many2one('project.team', string="Team")
    employee_ids = fields.Many2many(related="team_id.employee_ids", string="Employees")
    assignee_id = fields.Many2one('res.users', string="Assignee", domain="[('id', 'in', employee_ids)]",default=get_default_user)

    today_task_line_ids = fields.One2many('today.task.line', 'wizard_id', string="Today Task Line")
    overdue_task_line_ids = fields.One2many('overdue.task.line', 'wizard_id', string="Overdue Task Line")
    pending_task_line_ids = fields.One2many('pending.task.line', 'wizard_id', string="Pending Task Line")

    @api.onchange("assignee_id")
    def get_task_lines(self):
        today = date.today()
        today_lines = []
        overdue_lines = []
        pending_lines = []
        if self.assignee_id:
            emp_tasks = self.env['project.task'].search(
                [('user_ids', '=', self.assignee_id.id), ('stage_id.is_closed', '!=', True)])
            projects = list(set(emp_tasks.mapped('project_id')))
            for proj in projects:
                proj_tasks = emp_tasks.filtered(lambda x: x.project_id == proj)
                open_tasks = proj_tasks.filtered(
                    lambda x: x.date_deadline and x.date_deadline > today and not x.stage_id.is_hold)
                open_tasks_no_deadline = proj_tasks.filtered(lambda x: not x.date_deadline)
                today_tasks = proj_tasks.filtered(
                    lambda x: x.date_deadline and x.date_deadline == today and not x.stage_id.is_hold)
                overdue_tasks = proj_tasks.filtered(
                    lambda x: x.date_deadline and x.date_deadline < today and not x.stage_id.is_hold)
                for line in today_tasks:
                    today_lines.append((0, 0, {
                        'task_id': line.id,
                        'planned_hrs': line.allocated_hours
                        # 'planned_hrs': line.allocated_hours
                    }))
                for line in overdue_tasks:
                    overdue_lines.append((0, 0, {
                        'task_id': line.id,
                        'planned_hrs': line.allocated_hours
                    }))
                for line in open_tasks:
                    pending_lines.append((0, 0, {
                        'task_id': line.id,
                        'planned_hrs': line.allocated_hours
                    }))
                for line in open_tasks_no_deadline:
                    pending_lines.append((0, 0, {
                        'task_id': line.id,
                        'planned_hrs': line.allocated_hours
                    }))
        self.today_task_line_ids = [(5, 0, 0)]
        self.overdue_task_line_ids = [(5, 0, 0)]
        self.pending_task_line_ids = [(5, 0, 0)]
        self.today_task_line_ids = today_lines
        self.overdue_task_line_ids = overdue_lines
        self.pending_task_line_ids = pending_lines

    def action_add_today(self):
        pending_lines = self.pending_task_line_ids.filtered(lambda x: x.add_to)
        overdue_lines = self.overdue_task_line_ids.filtered(lambda x: x.add_to)
        today = date.today()
        if not pending_lines and not overdue_lines:
            raise ValidationError("There are no records selected to update.")
        if pending_lines:
            pending_lines.mapped('task_id').write({'date_deadline': today})
        if overdue_lines:
            overdue_lines.mapped('task_id').write({'date_deadline': today})
        action = self.env.ref('project_task_analysis.action_daily_task_assign').read()[0]
        action['target'] = 'new'
        action['context'] = {'default_team_id': self.team_id.id,
                             'default_assignee_id': self.assignee_id.id}
        return action

    @api.onchange('team_id')
    def update_assignees(self):
        for rec in self:
            if rec.team_id:
                rec.assignee_id = self.env.user.id if self.env.user.id in rec.employee_ids.ids else False


def kg_update_project_team(self):
    respl_team_id = self.env['project.team'].search([('is_resource_pool', '=', True)], limit=1)
    odoo_team_id = self.env['project.team'].search([('is_odoo', '=', True)], limit=1)
    employees_id = []
    employees_name = []
    team_id = self.env['project.team'].search([])
    team_assignees = team_id.mapped('employee_ids')
    task_id = self.env['project.task'].search([])
    assignees = task_id.mapped('user_ids')
    if assignees and team_assignees:
        if assignees not in team_assignees:
            for li in assignees:
                employees_id.append(li.id)
                employees_name.append(li.name)
    user_id = self.env['res.users'].search([('id', 'in', employees_id)])
    for usr in user_id:
        for vals in task_id:
            if usr in vals.user_ids:
                if vals.project_id:
                    if vals.project_id.is_resource_pool_project:
                        if respl_team_id:
                            respl_team_id.write({'employee_ids': [(6, 0, [usr.id])]})
                    else:
                        if odoo_team_id:
                            odoo_team_id.write({'employee_ids': [(6, 0, [usr.id])]})


class TodayTaskLine(models.Model):
    _name = 'today.task.line'

    wizard_id = fields.Many2one('daily.task.assign', string="Wizard")
    task_id = fields.Many2one('project.task', string="Task")
    state = fields.Many2one(related="task_id.stage_id", string="Status")
    project_id = fields.Many2one(related="task_id.project_id", string="Project")
    task_name = fields.Char(related="task_id.name", string="Task")
    planned_hrs = fields.Float(string="Planned Hrs")
    spent_hrs = fields.Float(related="task_id.effective_hours", string="Hours Spent")
    remaining_hrs = fields.Float(string="Remaining Hrs", compute="_compute_remaining")
    deadline = fields.Date(related="task_id.date_deadline", string="Deadline")
    start_date = fields.Date(related="task_id.date_start", string="Start Date")
    criticality = fields.Selection(related="task_id.criticality", string="Criticality")
    task_type = fields.Selection(related="task_id.task_type", string="Task Type")

    @api.onchange('planned_hrs')
    def _onchange_planned_hrs(self):
        self.task_id.allocated_hours = self.planned_hrs

    @api.depends('planned_hrs', 'spent_hrs')
    def _compute_remaining(self):
        for rec in self:
            rem_hrs = rec.planned_hrs - rec.spent_hrs
            rec.remaining_hrs = rem_hrs if rem_hrs > 0 else 0


class OverdueTaskLine(models.Model):
    _name = 'overdue.task.line'

    wizard_id = fields.Many2one('daily.task.assign', string="Wizard")
    task_id = fields.Many2one('project.task', string="Task")
    state = fields.Many2one(related="task_id.stage_id", string="Status")

    project_id = fields.Many2one(related="task_id.project_id", string="Project")
    task_name = fields.Char(related="task_id.name", string="Task")
    planned_hrs = fields.Float(string="Planned Hrs")
    spent_hrs = fields.Float(related="task_id.effective_hours", string="Hours Spent")
    deadline = fields.Date(related="task_id.date_deadline", string="Deadline")
    start_date = fields.Date(related="task_id.date_start", string="Start Date")
    criticality = fields.Selection(related="task_id.criticality", string="Criticality")
    task_type = fields.Selection(related="task_id.task_type", string="Task Type")
    add_to = fields.Boolean("Add to Today")

    @api.onchange('planned_hrs')
    def _onchange_planned_hrs(self):
        self.task_id.allocated_hours = self.planned_hrs


class PendingTaskLine(models.Model):
    _name = 'pending.task.line'

    wizard_id = fields.Many2one('daily.task.assign', string="Wizard")
    task_id = fields.Many2one('project.task', string="Task")
    state = fields.Many2one(related="task_id.stage_id", string="Status")

    project_id = fields.Many2one(related="task_id.project_id", string="Project")
    task_name = fields.Char(related="task_id.name", string="Task")
    planned_hrs = fields.Float(string="Planned Hrs")
    spent_hrs = fields.Float(related="task_id.effective_hours", string="Hours Spent")
    deadline = fields.Date(related="task_id.date_deadline", string="Deadline")
    start_date = fields.Date(related="task_id.date_start", string="Start Date")
    criticality = fields.Selection(related="task_id.criticality", string="Criticality")
    task_type = fields.Selection(related="task_id.task_type", string="Task Type")
    add_to = fields.Boolean("Add to Today")

    @api.onchange('planned_hrs')
    def _onchange_planned_hrs(self):
        self.task_id.allocated_hours = self.planned_hrs


