# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ProjectStatus(models.Model):
    _inherit = 'project.team'
    _description = 'Configuring employees'

    employee_ids = fields.Many2many('res.users')

    is_resource_pool = fields.Boolean('is Resource Pool')
    is_odoo = fields.Boolean('is Odoo Team')
    allocation_lines = fields.One2many('kg.resource.allocation', 'team_id')
    pool_lines = fields.One2many('resource.pool', 'team_id')

    edit_readonly = fields.Boolean('Edit/Readonly', default=False)

    running_project = fields.Integer(string="Running Project :", compute='compute_running_project')
    running_engagement = fields.Integer(string="Running Resource Engagements :", compute='compute_running_engagement')

    def action_edit_readonly(self):
        for rec in self:
            rec.edit_readonly = not rec.edit_readonly


    @api.depends('allocation_lines.project_id')
    def compute_running_project(self):
        for record in self:
            non_engagement_projects = set()
            for line in record.allocation_lines:
                if line.project_id and not line.project_id.is_engagement_project:
                    non_engagement_projects.add(line.project_id.id)
            record.running_project = len(non_engagement_projects)


    @api.depends('allocation_lines.project_id')
    def compute_running_engagement(self):
        for record in self:
            engagement_projects = set()
            for line in record.allocation_lines:
                if line.project_id and line.project_id.is_engagement_project:
                    engagement_projects.add(line.project_id.id)
            record.running_engagement = len(engagement_projects)



class ProjectTypeInh(models.Model):
    _inherit = 'project.task.type'

    is_closed = fields.Boolean('Closing Stage', help="Tasks in this stage are considered as closed.")
    is_hold = fields.Boolean(string="Hold Stage")
    is_fixed = fields.Boolean(string="Fixed Stage")
    is_progress = fields.Boolean(string="In Progress Stage")

    is_check_task_status = fields.Boolean(string='Check task Status', help='Helps to check the status of task')


class ResourcePool(models.Model):
    _name = 'resource.pool'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    team_id = fields.Many2one('project.team', string="Project Team")
    resource_id = fields.Many2one('res.users', string="Resource")
    project_id = fields.Many2one('project.project', string="Project")
    deadline = fields.Date(string="Deadline")
    task = fields.Char(string="Task")
    planned_hrs = fields.Float(string='Planned Hours')
    comments = fields.Char(string='Comments', compute='compute_statess')

    @api.depends('resource_id')
    def compute_statess(self):
        for rec in self:
            if rec.resource_id:
                task_ids = self.env['resource.task.line'].sudo().search([('resource_id', '=', rec.resource_id.id)])
                send_request_found = any(task.resource_pool_id.state == 'send' for task in task_ids)
                rec.comments = 'A New Request is Send' if send_request_found else ''
            else:
                rec.comments = ''


class KgResourceAllocation(models.Model):
    _name = 'kg.resource.allocation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'resource_id'

    team_id = fields.Many2one('project.team', string="Project Team")
    resource_id = fields.Many2one('res.users', string="Resource")
    team_lead_id = fields.Many2one('res.users', string="Team Lead")
    project_id = fields.Many2one('project.project', string="Project")
    engagement_model = fields.Selection([('resource_mnt', 'Resource Management'),
                                         ('bug_fixing', 'Bug Fixing'),
                                         ('documentation', 'Documentation'),
                                         ('development', 'Development'),
                                         ('add_support', 'Add Support'),
                                         ('testing', 'Testing')], string="Engagement Model")
    period = fields.Many2one('kg.period', string="Period")
    start_date = fields.Date(string="Start Date", tracking=True)
    end_date = fields.Date(string="End Date", tracking=True)
    # current_date = fields.Date(string="Current Date", default=fields.Date.context_today)
    status = fields.Selection([('open', 'Open'),
                               ('in_progress', 'In Progress'),
                               ('completed', 'Completed'),
                               ('hold', 'Hold'),
                               ], string="Status", default="open")
    planned_hrs = fields.Float(string='Planned Hours')
    comments = fields.Char(string='Comments')

    # @api.onchange('resource_id', 'start_date', 'end_date')
    # def onchange_allocation_lines(self):
    #     """To show warning in allocation line if the resource already in allocation"""
    #     for record in self:
    #         if record.resource_id and record.start_date and record.end_date:
    #             overlapping_allocations = self.search([
    #                 ('resource_id', '=', record.resource_id.id),
    #                 ('start_date', '<=', record.end_date),
    #                 ('end_date', '>=', record.start_date)
    #             ])
    #
    #             if overlapping_allocations:
    #                 raise ValidationError(
    #                     "This resource is already allocated for the specified date range. Please select a different date range or resource."
    #                 )


class ProjectTaskInh(models.Model):
    _inherit = 'project.task'

    resource_id = fields.Many2one('project.resource.pool')
    description = fields.Html(string='Description', sanitize_attributes=False, copy=False)
    is_main_task = fields.Boolean(default=False)


class ProjectProjectInh(models.Model):
    _inherit = 'project.project'

    is_team_pool = fields.Boolean(string="Is Resource Pool")
    # company_ids = fields.Many2many('res.company','company_rel',string="Visible Companies")

    parent_id = fields.Many2one('project.project', string="Parent Project")

    child_project_count = fields.Integer(string="Sub-project", compute="_compute_child_project_count", )

    def action_create_sub_project(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'New Sub-Project',
            'res_model': 'project.project',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_parent_id': self.id,
            },
        }

    @api.depends('parent_id')
    def _compute_child_project_count(self):
        for project in self:
            project.child_project_count = self.env['project.project'].sudo().search_count([('parent_id', '=', project.id)])

    def action_view_child_projects(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sub-Projects',
            'view_mode': 'kanban,tree,form',
            'res_model': 'project.project',
            'domain': [('parent_id', '=', self.id)],
            'context': {
                'default_parent_id': self.id,
                'create': False,
            },
            'target': 'current',
        }


class KgPeriod(models.Model):
    _name = 'kg.period'

    name = fields.Char(string="Period")
