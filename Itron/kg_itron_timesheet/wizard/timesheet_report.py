# -*- coding: utf-8 -*-

from odoo import fields, models, api
from datetime import date

from odoo.exceptions import UserError


class TimesheetReport(models.TransientModel):
    """Create a Transient model for Timesheet Report Wizard"""
    _name = 'timesheet.report'
    _description = 'Timesheet Report Wizard'

    company_id = fields.Many2one(
        'res.company',
        string="Company",
        default=lambda self: self.env.company,
        help="Select the company for the report")
    user_id = fields.Many2many(
        'res.users',
        string="Employee",
        help="Select the employee for the timesheet report", domain=lambda self: self._get_user_domain())
    employee_id = fields.Many2one(
        'hr.employee',
        string="Employee",
        help="Select the employee for the timesheet report",)

    from_date = fields.Date(
        string="Starting Date",
        default=date.today(),
        help="Select the starting date for the report")

    to_date = fields.Date(
        string="Ending Date",
        default=date.today(),
        help="Select the ending date for the report")

    # New fields
    project_id = fields.Many2many(
        'project.project',
        string="Projects",
        help="Select the projects to include in the report")

    @api.model
    def _get_user_domain(self):
        """Return domain to filter users based on logged-in user's team and company."""
        current_user = self.env.user
        print("current_user:", current_user)

        teams = self.env['project.team'].search([('timesheet_user_ids', '=', current_user.id)])
        print("teams:", teams)
        current_company = current_user.company_id
        print("current_company:", current_company)
        domain = []
        if teams:
            team_member_ids = teams.mapped('employee_ids').ids
            print("team_member_ids:", team_member_ids)
            domain.append(('id', 'in', team_member_ids))
        if current_company:
            domain.append(('company_id', '=', current_company.id))

        print("final_domain:", domain)
        return domain

    def print_timesheet(self):
        """Redirects to the report with the values obtained from the wizard."""
        if not self.from_date or not self.to_date:
            raise UserError("Please provide both starting and ending dates.")
        if self.from_date > self.to_date:
            raise UserError("Starting date cannot be later than the ending date.")

        is_single_employee = len(self.user_id) == 1
        is_single_project = len(self.project_id) == 1

        data = {
            'employee': self.employee_id.id,  # Handle multiple employees
            'start_date': self.from_date,
            'end_date': self.to_date,
            'projects': self.project_id.ids if self.project_id else [],
            'company': self.company_id.id if self.company_id else False,
            'is_same_date': self.from_date == self.to_date,
            'is_single_employee': is_single_employee,
            'is_single_project': is_single_project

        }
        return self.env.ref(
            'kg_itron_timesheet.action_report_print_timesheets'
        ).report_action(self, data=data)
