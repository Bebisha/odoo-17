from odoo import models, fields, _
from odoo.exceptions import ValidationError


class AllocatedUnallocatedEmployees(models.TransientModel):
    _name = "allocated.unallocated.employees"
    _description = "Allocated Unallocated Employees"

    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company)

    def action_print_report(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError(_('Start Date must be less than End Date'))

        allocated_employees = []
        unallocated_employees = []

        timesheet_ids = self.env['account.analytic.line'].search([
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date),
            ('company_id', '=', self.company_id.id),
        ])
        if timesheet_ids:
            allocated_employee_ids = timesheet_ids.mapped('employee_id').filtered(
                lambda x: x.staff_worker == 'technical')
            if allocated_employee_ids:
                for alo_emp in allocated_employee_ids:
                    allocated_employees.append({
                        'employee_no': alo_emp.employee_no,
                        'name': alo_emp.name
                    })
            employee_ids = self.env['hr.employee'].search([('staff_worker', '=', 'technical')])
            if employee_ids:
                unallocated_employee_ids = employee_ids - allocated_employee_ids
                if unallocated_employee_ids:
                    for unalo_emp in unallocated_employee_ids:
                        unallocated_employees.append({
                            'employee_no': unalo_emp.employee_no,
                            'name': unalo_emp.name
                        })

        if not allocated_employees:
            raise ValidationError(_('No data in this date range'))

        data = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'company_name': self.company_id.name,
            'company_zip': self.company_id.zip,
            'company_state': self.company_id.state_id.name,
            'company_country': self.company_id.country_id.name,
            'allocated_employees': allocated_employees,
            'unallocated_employees': unallocated_employees
        }

        return self.env.ref('kg_allocated_unallocated_employees.action_allocated_unallocated_report').with_context(
            landscape=False).report_action(self, data=data)
