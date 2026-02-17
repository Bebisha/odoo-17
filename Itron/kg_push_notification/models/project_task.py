from odoo import models, api


class ProjectTask(models.Model):
    _inherit = 'project.task'

    @api.model
    def create(self, values):
        res = super(ProjectTask, self).create(values)
        active_line = self.env.user.login_ids.filtered(lambda x: x.is_active)
        x = 0
        for i in active_line:
            if i.device_id:
                x += 1
                message_body = "You have created a new task\nTask name: " + res.name
                # self.env['push.notification'].send_push_notification(user_id=self.env.user.id, device_id=i.device_id,
                #                                                      message_title='Task Created',
                #                                                      message_body=message_body, res_model_id=res.id,
                #                                                      res_model_name='project.task')
        return res
