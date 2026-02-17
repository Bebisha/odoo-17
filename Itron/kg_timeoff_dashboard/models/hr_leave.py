# -*- coding: utf-8 -*-
from odoo import api, models


class HRLeave(models.Model):
    _inherit = 'hr.leave'

    def check_qualified_for_second_approver(self):
        user =self.env.user.sudo()
        if user.has_group('kg_attendance.all_approval_access'):
            return True
        if user.id in self.sudo().holiday_status_id.sudo().responsible_ids.ids:
            return True


        return False

    @api.model
    def get_values(self, args=None):
        """ Fetch leave records based on specific states """
        leave_data = []
        is_admin = self.env.user.has_group('base.group_system')
        is_cto = self.env.user.has_group('kg_timeoff_dashboard.group_admin_india_dashboard')
        print(is_cto, 'pppppppppppppppppppppppppppppp')
        leaves = []
        if is_cto:
            leaves = self.env['hr.leave'].sudo().search([
                ('state', 'in', ['confirm', 'validate1', 'validate3']),
                ('employee_id.company_id', '=', self.env.user.company_id.id)
            ])
        elif not is_admin:
            leaves = self.env['hr.leave'].sudo().search([('state', 'in', ['confirm', 'validate1', 'validate3']),('employee_id.leave_manager_id', '=', self.env.user.id)])

        else:
            leaves = self.env['hr.leave'].sudo().search([('state', 'in', ['confirm', 'validate1', 'validate3'])])
        for leave in leaves:
            employee = leave.employee_id
            state = dict(leave._fields['state'].selection).get(leave.state,
                                                               '') if leave else ''
            leave_data.append({
                'id': leave.id,
                'employee_id': leave.employee_id.name,
                'company': leave.company_id.name,
                'company_id': leave.company_id.id,
                'reason': leave.name or "No reason given",
                'holiday_status_id': leave.holiday_status_id.name,
                'request_date_from': leave.request_date_from.strftime('%d/%m/%Y') if leave.request_date_from else '',
                'request_date_to': leave.request_date_to.strftime('%d/%m/%Y') if leave.request_date_to else '',
                'number_of_days_display': leave.number_of_days_display,
                'state': state,
                'leaves': [leave.id for leave in leaves if leave.employee_id.id == employee.id],
            })

        company_data = []
        # companies = self.env['res.company'].sudo().search([])
        companies=self.env.user.sudo().company_ids

        for company in companies:
            company_data.append({
                'id': company.id,
                'name': company.name,
                'country_code': company.country_id.code if company.country_id else '',
            })

        return {
            'leaves': leave_data,
            'companies': company_data,
        }
