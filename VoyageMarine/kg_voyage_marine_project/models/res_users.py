from odoo import models, fields, api
import datetime


class KGProjectResUsersInherit(models.Model):
    _inherit = "res.users"

    kg_is_task_assigned = fields.Boolean(string="Is Task Assigned", compute="compute_kg_is_task_assigned", store=True)

    @api.depends('name')
    def compute_kg_is_task_assigned(self):
        today = datetime.datetime.now()
        for rec in self:
            rec.kg_is_task_assigned = False
            user_task_ids = self.env["project.task"].search([
                ('user_ids', 'in', rec.id)
            ])
            task_ids = user_task_ids.filtered(lambda x: x.planned_date_begin and x.date_deadline and (
                    (x.planned_date_begin <= today <= x.date_deadline) or
                    (x.planned_date_begin >= today and x.date_deadline >= today)
            ))
            rec.kg_is_task_assigned = bool(task_ids)

