# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
import base64

from odoo import models, fields, tools


class LeaveBalanceReport(models.Model):
    """Balance Leave Report model"""

    _name = 'report.balance.leave'
    _description = 'Leave Balance Report'
    _auto = False

    emp_id = fields.Many2one('hr.employee', string="Employee", readonly=True)
    employee_no = fields.Char(string='Employee Number')
    gender = fields.Char(string='Gender', readonly=True)
    department_id = fields.Many2one('hr.department', string='Department', readonly=True)
    country_id = fields.Many2one('res.country', string='Nationality', readonly=True)
    job_id = fields.Many2one('hr.job', string='Job', readonly=True)
    leave_type_id = fields.Many2one('hr.leave.type', string='Leave Type', readonly=True)
    allocated_days = fields.Integer('Accrued Leave')
    taken_days = fields.Integer('Taken Leaves')
    balance_days = fields.Integer('Remaining Balance')
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company)


    def init(self):
        """Loads report data"""
        tools.drop_view_if_exists(self._cr, 'report_balance_leave')
        self._cr.execute("""
            CREATE or REPLACE view report_balance_leave as (
            SELECT 
                row_number() over(ORDER BY e.id) as id,
                e.id AS emp_id,
                e.employee_no AS employee_no,  -- Added employee_no field
                e.gender as gender,
                e.country_id as country_id,
                e.department_id as department_id,
                e.job_id as job_id,
                lt.id AS leave_type_id,
                SUM(al.number_of_days) AS allocated_days,
                COALESCE(taken_days.taken_days, 0) AS taken_days,
                SUM(al.number_of_days) - COALESCE(taken_days.taken_days, 0) AS balance_days,
                e.company_id as company_id
            FROM
                hr_employee e
                JOIN hr_leave_allocation al ON al.employee_id = e.id
                JOIN hr_leave_type lt ON al.holiday_status_id = lt.id
                LEFT JOIN (
                    SELECT
                        l.employee_id,
                        l.holiday_status_id,
                        SUM(l.number_of_days) AS taken_days
                    FROM
                        hr_leave l
                    WHERE
                        l.state = 'validate'
                    GROUP BY
                        l.employee_id,
                        l.holiday_status_id
                ) AS taken_days ON taken_days.employee_id = e.id AND taken_days.holiday_status_id = lt.id
            WHERE
                e.active = True
            GROUP BY
                e.id,
                e.employee_no,
                lt.id,
                taken_days.taken_days
            )
            """)

    def leave_balance_pdf(self):
        """ PDF report for leave balance """
        values = []
        for rec in self:
            vals = {
                'employee': rec.emp_id.name,
                'department': rec.department_id.name,
                'job': rec.job_id.name,
                'leave_type': rec.leave_type_id.name,
                'allocated_days': rec.allocated_days,
                'taken_days': rec.taken_days,
                'balance_days': rec.balance_days
            }
            values.append(vals)

        data = {
            'company_id': self.company_id.name,
            'value_list': values,
        }
        return self.env.ref('kg_hr_holidays_balance_report.action_report_leave_balance_pdf').with_context(
            landscape=True).report_action(self, data=data)
