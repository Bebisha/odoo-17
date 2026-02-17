from odoo import models, api,fields
import json


class KGProjectTaskGannt(models.Model):
    _inherit = "project.task"


    reason = fields.Text(string="Reason", tracking=True)
    task_status = fields.Text(string="Task Status", tracking=True)


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

                    if task.planned_date_begin and task.date_deadline:
                        duration = abs(task.planned_date_begin- task.date_deadline).days
                        duration = f"{duration}days" if duration else "0 days"
                    else:
                        duration = " "
                    item.update({
                        # 'assigned_user': assigned_user,
                        'assigned_user': task.project_id.Coordinator_id.name if task.project_id.Coordinator_id else '',

                        'parent':  task.parent_id.name if task.parent_id else '',
                        'progress': progress,
                        'duration': duration,
                        'start_date': start_date,
                        'end_date': end_date,
                        'reason': task.reason if task.reason else '',
                    })
        return rows


