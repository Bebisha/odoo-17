from odoo import fields, models, api


class ProjectTeam(models.Model):
    _name = 'project.team'

    _description = 'Project Team'

    name = fields.Char(string='Team Name')
    parent_id = fields.Many2one('project.team', string='Parent')
    manager_id = fields.Many2one('res.users', string='Manager')
    timesheet_user_ids = fields.Many2many('res.users','rec_id', string='Timesheet Users', copy=False)
