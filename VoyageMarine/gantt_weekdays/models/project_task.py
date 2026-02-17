from odoo import models, api
import json


class KGProjectTaskGannt(models.Model):
    _inherit = "project.task"

    @api.model
    def get_gannt_values(self, rows):
        for item in rows:
            ids = json.loads(item['id'])
            project_id = next((entry['project_id'][0] for entry in ids if 'project_id' in entry), '')
            task_id = next((entry['name'] for entry in ids if 'name' in entry), '')

            if project_id and task_id:
                task = self.search([('name', '=', task_id), ('project_id.id', '=', project_id)], limit=1)
                if task:
                    assigned_user = ', '.join(user.name for user in task.user_ids) if task.user_ids else ''
                    progress = f"{int(task.progress)}%" if task.progress else ''
                    start_date = task.planned_date_begin.strftime('%d/%m/%Y') if task.planned_date_begin else ''
                    end_date = task.date_deadline.strftime('%d/%m/%Y') if task.date_deadline else ''
                    item.update({
                        'assigned_user': assigned_user,
                        'progress': progress,
                        'start_date': start_date,
                        'end_date': end_date,
                    })
        return rows
