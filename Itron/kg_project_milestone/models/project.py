from odoo import fields, models, api, _
from vobject import readOne


class Project(models.Model):
    _inherit = 'project.project'

    project_team_id = fields.Many2one('project.team', string='Project Team')
    user_id = fields.Many2one('res.users', string='Project Manager', default=lambda self: self.env.user, tracking=True,
                              company_dependent=True)
    project_logo = fields.Image(string="Project Logo", max_width=1024, max_height=1024)
    project_active = fields.Boolean(string="Running Project")


    def action_view_milestone(self):
        action = self.with_context(active_id=self.id, active_ids=self.ids) \
            .env.ref('kg_project_milestone.milestone_menu_action') \
            .sudo().read()[0]
        action['domain'] = [('project_id', '=', self.id)]
        return action

    def view_project_update(self):
        return {
            'name': _('Project Update'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'project.update.wizard',
            'views': [(self.env.ref('kg_project_milestone.view_project_update_form').id, 'form')],
            'view_id': self.env.ref('kg_project_milestone.view_project_update_form').id,
            'target': 'new'
        }


class TaskStage(models.Model):
    _inherit = 'project.task.type'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company)


class ProjectUpdate(models.Model):
    _inherit = 'project.update'

    milestone_id = fields.Many2one('project.milestone', string="Milestone")
    time_line_id = fields.Many2one('timeline.line', string="Activity")
