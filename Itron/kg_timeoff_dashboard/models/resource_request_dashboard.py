from odoo import models, fields, api
from datetime import date, timedelta


class KgPoolDashboard(models.Model):
    _inherit = 'project.resource.pool'

    def resource_request_dashboard(self, company_id=None):
        user = self.env.user
        today = fields.Date.today()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        is_admin = user.has_group('base.group_system')
        state_mapping = {
            'draft': 'Draft',
            'confirm': 'Confirm',
            'send': 'Request Sent',
            'approve': 'Approved',
            'reject': 'Rejected',
            'discuss': 'Discuss',
        }

        domain = [
            ('state', 'in', ['send', 'approve', 'reject'])
        ]
        if company_id:
            domain.append(('company_id', '=', company_id))

        teams = self.env['project.team'].sudo().search([('timesheet_user_ids', '=', user.id)])
        is_cto = user.has_group('kg_timeoff_dashboard.group_admin_india_dashboard')
        companies = self.env['res.company'].sudo().search([])


        if is_cto:
            employee_ids = self.env['hr.employee'].sudo().search([
                ('company_id', '=', self.env.company.id)
            ]).mapped('user_id').ids
            domain.append(('users_id', 'in', employee_ids))
            companies = self.env['res.company'].sudo().search([('id', '=', self.env.company.id)])

        elif not is_admin and teams:
            user_ids = teams.mapped('employee_ids').ids
            domain.append(('users_id', 'in', user_ids))
        elif not is_admin and not teams:
            domain.append(('users_id', 'in', user.ids))
        else:
            team_member_ids = self.env['res.users'].sudo().search([]).ids
            domain.append(('users_id', 'in', team_member_ids))

        resource_requests = self.sudo().search(domain)
        used_state = list(set(resource_requests.mapped('state')))
        full_state_selection = dict(self._fields['state'].selection)
        state_val = [(key, full_state_selection[key]) for key in used_state if key in full_state_selection]

        print("used_state",used_state,full_state_selection)
        # status = [
        #     val for key, val in resource_requests
        #     .fields_get(allfields=['state'])['state']['selection']
        # ]


        result_data = [
            {
                'id': resource.id,
                'ref_no': resource.name,
                'requester': resource.users_id.name or 'Unknown',
                'company': resource.company_id.name or 'Unknown',
                'company_id': resource.company_id.id,
                'project': resource.project_id.name or 'Unknown',
                'assignee': ', '.join(resource.user_ids.mapped('name')) or 'Unknown',
                'start_date': resource.date_start,
                'end_date': resource.date_end,
                'status': state_mapping.get(resource.state, 'Unknown'),
                'status_key': resource.state,
            }
            for resource in resource_requests
        ]

        company_data = [{'id': company.id, 'name': company.name} for company in companies]
        # print("result_data",result_data,)

        return {
            'resource_requests': result_data,
            'companies': company_data,
            'status' : state_val ,
        }