

from odoo import api, fields, models, _
from odoo.exceptions import UserError,ValidationError
from odoo.addons.website.tools import text_from_html


STATUS_DICT = {'on_track': 'On Track', 'at_risk': 'At Risk', 'off_track': 'Off Track', 'on_hold': 'On Hold','done':'Done'}


class ProjectUpdate(models.TransientModel):
    _name = "project.update.wizard"
    _description = "Project Update Wizard"

    def get_milestone_status(self):
        project_id = self.env['project.project'].browse(self._context.get('active_ids', [])).id
        milestones = self.env['project.milestone'].search([('project_id', '=', project_id), ('is_reached', '=', False)],
                                                          order="deadline asc")
        btn = '<button class="btn btn-primary" type="button" name="view_tasks" icon="fa-tasks">Views Tasks</button>'
        content = '<br/><table border=1 style="padding: 0.75rem;">' \
                  '<tbody><tr><th width=70% style=font-color:#0f7deb>Milestone</th>' \
                  '<th width=20% style="font-color:#0f7deb;padding: 0.75rem;">Deadline</th>' \
                  '<th width=10% style="font-color:#0f7deb;padding: 0.75rem;">Total Tasks</th>' \
                  '<th  width=10% style="font-color:#0f7deb;padding: 0.75rem;">Open Tasks</th></tr>'
        for ml in milestones:
            tasks = self.env['project.task'].search([('milestone_ids','=',ml.id)])
            total_task_count = 0
            open_task_count = 0
            if tasks:
                total_task_count = len(tasks)
                open_task_count = len(tasks.filtered(lambda l: l.stage_id.is_closed == False))
            content += '<tr><td style="padding: 0.75rem;">'+str(ml.name)+\
                       '</td><td style="padding: 0.75rem;">'+str(ml.deadline)+\
                       '</td><td style="padding: 0.75rem;">'+str(total_task_count)+\
                       '</td><td style="padding: 0.75rem;">'+str(open_task_count)+'</td></tr>'
        content += '</tbody></table><p><br></p>'

        return content


    def get_default_history(self):
        project_id = self.env['project.project'].browse(self._context.get('active_ids', [])).id
        updates = self.env['project.update'].search([('project_id','=',project_id)],limit=10,order ='date desc')
        content = '<br/><table border=1 style="padding: 0.75rem;">' \
                  '<tbody><tr><th width=15% style=font-color:#0f7deb>Update</th>' \
                  '<th width=10% style="font-color:#0f7deb;padding: 0.75rem;">Date</th>' \
                  '<th width=10% style="font-color:#0f7deb;padding: 0.75rem;">Status</th>' \
                  '<th  width=65% style="font-color:#0f7deb;padding: 0.75rem;">Detailed Update</th></tr>'
        for upd in updates:
            desc = text_from_html(upd.description)
            content += '<tr><td style="padding: 0.75rem;">'+str(upd.name)+\
                       '</td><td style="padding: 0.75rem;">'+str(upd.date)+\
                       '</td><td style="padding: 0.75rem;">'+str(STATUS_DICT[upd.status])+\
                       '</td><td style="padding: 0.75rem;">'+desc+'</td></tr>'
        content += '</tbody></table><p><br></p>'
        return content

    def view_open_tasks(self):
        project_id = self.env['project.project'].browse(self._context.get('active_ids', [])).id
        milestones = self.env['project.milestone'].search([('project_id', '=', project_id), ('is_reached', '=', False)],
                                                          order="deadline asc")
        action = self.env.ref('project.action_view_all_task').sudo().read()[0]
        action['domain'] = [('milestone_ids', 'in', milestones.ids), ('stage_id.is_closed', '=', False)]
        return action

    # def view_all_tasks(self):
    #     project_id = self.env['project.project'].browse(self._context.get('active_ids', [])).id
    #     milestones = self.env['project.milestone'].search([('project_id', '=', project_id), ('is_reached', '=', False)],
    #                                                       order="deadline asc")
    #     action = self.env.ref('project.action_view_all_task').sudo().read()[0]
    #     action['domain'] = [('milestone_ids', 'in', milestones.ids)]
    #     return action


    name = fields.Char(required=False, string='Subject')
    status = fields.Selection(selection=[
        ('on_track', 'On Track'),
        ('at_risk', 'At Risk'),
        ('off_track', 'Off Track'),
        ('on_hold', 'On Hold')
    ], required=False, tracking=True,default='on_track')
    date = fields.Date(default=fields.date.today(),required=False)
    status_update =  fields.Html(required=False)
    previous_status = fields.Html(default=get_default_history,readonly=True,string='Previous History')
    milestone_status = fields.Html(default=get_milestone_status,readonly=True,string='Milestone')

    def create_project_update(self):
        if not self.name:
            raise ValidationError("Please add Subject!")
        if not self.status:
            raise ValidationError("Status is Status!")
        if not self.date:
            raise ValidationError("Date is Date!")
        if not self.status_update:
            raise ValidationError("Name is some content!")
        project_id = self.env['project.project'].browse(self._context.get('active_ids', [])).id
        self.env['project.update'].sudo().create({'project_id':project_id,'status':self.status,'name':self.name,'date':self.date,'description':self.status_update})

