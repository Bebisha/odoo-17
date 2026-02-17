# -*- coding: utf-8 -*-

from odoo import models, api, fields, _


class KgProject(models.Model):
    _inherit = 'project.project'

    project_team_user_ids = fields.Many2many(
        'res.users', 'project_team_user_rel', 'project_id', 'user_id',
        string='Team Members', default=lambda self: [(4, self.env.user.id)])
    company_ids = fields.Many2many('res.company','company_rel',string="Visible Companies",default=lambda self: self.env.company)

    billing_type = fields.Selection(
        compute="_compute_billing_type",
        selection=[
            ('not_billable', 'not billable'),
            ('manually', 'billed manually'),
        ],
        default='not_billable',
        required=False,
        readonly=False,
        store=True,
    )


class KgProjectTask(models.Model):
    _inherit = 'project.task'

    milestone_ids = fields.Many2one('project.milestone', string="Milestone")
    time_line_id = fields.Many2one('timeline.line', string="Activity")
    time_line_ids = fields.Many2many('timeline.line')

    @api.onchange('milestone_ids')
    def onchange_mileston_ids(self):
        project = self.project_id
        if project and self.milestone_ids:
            time_line_ids = self.env['timeline.line'].sudo().search([
                ('project_rel_id', '=', project.id),
                ('milestone_id', '=', self.milestone_ids.id)
            ])
            self.time_line_ids = [(6, 0, time_line_ids.ids)]
        else:
            self.time_line_ids = [(6, 0, [])]

    @api.model_create_multi
    def create(self, vals_list):
        rec = super(KgProjectTask, self.with_context(mail_notrack=True)).create(vals_list)
        if rec.parent_id:
            rec.milestone_ids = rec.parent_id.milestone_ids.id
        return rec


    def write(self, values):
        # Add code here
        return super(KgProjectTask, self.with_context(mail_notrack=True)).write(values)
