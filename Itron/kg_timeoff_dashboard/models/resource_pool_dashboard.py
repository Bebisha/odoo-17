from datetime import date, timedelta
from odoo import models, fields, api


class KgPoolDashboard(models.Model):
    _inherit = 'project.task'

    def resource_pool_dashboard(self):
        today = date.today()
        end_of_range = today + timedelta(days=6)

        user = self.env.user
        is_admin = user.has_group('base.group_system')
        teams = self.env['project.team'].search([('timesheet_user_ids', '=', user.id)])

        domain = [
            # ('end_date', '>=', today),
            # ('end_date', '<=', end_of_range),
        ]
        user_company_id = self.env.company.id
        is_cto = user.has_group('kg_timeoff_dashboard.group_admin_india_dashboard')

        if is_cto:
            employee_ids = self.env['hr.employee'].sudo().search([
                ('company_id', '=', user_company_id)
            ]).mapped('user_id').ids
            domain.append(('resource_id', 'in', employee_ids))

        elif not is_admin and teams:
            user_ids = teams.mapped('employee_ids').ids
            domain.append(('resource_id', 'in', user_ids))
        elif not is_admin and not teams:
            domain.append(('resource_id', 'in', user.ids))
        else:
            team_member_ids = self.env['res.users'].sudo().search([]).ids
            domain.append(('resource_id', 'in', team_member_ids))

        tasks = self.env['kg.resource.allocation'].sudo().search(domain)

        project_employee_map = {}
        task_details = []

        # Retrieve the resource pool lines separately
        resource_pool_obj = self.env['project.team'].sudo().search([('is_resource_pool', '=', True)], limit=1)
        pool_lines = resource_pool_obj.pool_lines.filtered(lambda x: x.resource_id.id != False)

        # Create a map for pool lines to make them easily accessible
        pool_lines_map = {}
        for line in pool_lines:
            pool_lines_map[line.resource_id.id] = {
                'resource_name': line.resource_id.name,
                'resource_id': line.resource_id.id,
                'pool_id': line.id,
            }

        for task in tasks:
            for user in task.resource_id:
                key = (task.project_id.id, user.id)
                if key not in project_employee_map:
                    project_employee_map[key] = {
                        'id': task.id,
                        'employee_name': user.name,
                        'project_id': task.project_id.id,
                        'team_lead_id': task.team_lead_id.id,
                        'team_lead_name': task.team_lead_id.name,
                        'project_name': task.project_id.name,
                        'engagement_model': dict(task._fields['engagement_model'].selection).get(task.engagement_model),
                        'status': dict(task._fields['status'].selection).get(task.status),
                        'start_date': task.start_date.strftime('%d/%m/%Y') if task.start_date else '',
                        'end_date': task.end_date.strftime('%d/%m/%Y') if task.end_date else '',
                        'pool_lines': [pool_lines_map.get(user.id)]  # Associate the pool line with the user
                    }

            if not task.resource_id:
                key = (task.project_id.id, None)
                if key not in project_employee_map:
                    project_employee_map[key] = {
                        'id': task.id,
                        'employee_name': 'Unassigned',
                        'project_id': task.project_id.id,
                        'project_name': task.project_id.name,
                        'team_lead_id': task.team_lead_id.id,
                        'team_lead_name': task.team_lead_id.name,
                        'engagement_model': dict(task._fields['engagement_model'].selection).get(task.engagement_model),
                        'status': dict(task._fields['status'].selection).get(task.status),
                        'start_date': task.start_date.strftime('%d/%m/%Y') if task.start_date else '',
                        'end_date': task.end_date.strftime('%d/%m/%Y') if task.end_date else '',
                        'pool_lines': []  # No pool lines for unassigned tasks
                    }

        task_details = list(project_employee_map.values())
        print(task_details,'ppppppppppppppppp')

        unique_project_ids = set(entry['project_id'] for entry in task_details)
        print(unique_project_ids,'pppppppppppppp')

        running_project_ids = self.env['project.project'].sudo().search([
            ('id', 'in', list(unique_project_ids)),
            ('project_active', '=', True)
        ]).ids
        engagement_project_ids = self.env['project.project'].sudo().search([
            ('id', 'in', list(unique_project_ids)),
            ('is_engagement_project', '=', True)
        ]).ids

        running_project_count = len(running_project_ids)
        engagement_project_count = len(engagement_project_ids)
        print(running_project_count,'ppppppppppppp')

        return {
            'task_details': task_details,
            'pool_lines': list(pool_lines_map.values()),  # Return pool lines separately
            'running_count': running_project_count,
            'engagement_count': engagement_project_count,
            'running_project': list(running_project_ids),
            'engagement_project': engagement_project_ids,
        }
