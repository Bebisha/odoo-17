from datetime import date, datetime
import calendar
from odoo import models, fields
from odoo.exceptions import ValidationError


class GenerateEmployeeEntriesWizard(models.TransientModel):
    _name = "generate.employee.entries.wizard"
    _description = "Generate Employee Entries Wizard"

    def default_start_date(self):
        today = date.today()
        current_month = today.month
        current_year = today.year
        return datetime(current_year, current_month, 1).date()

    def default_end_date(self):
        today = date.today()
        current_month = today.month
        current_year = today.year
        last_day = calendar.monthrange(current_year, current_month)[1]
        return datetime(current_year, current_month, last_day)

    name = fields.Char(string="Reference")
    start_date = fields.Date(string="Start Date", default=default_start_date)
    end_date = fields.Date(string="End Date", default=default_end_date)
    entry_type = fields.Selection([('overseas', 'Overseas'), ('anchorage', 'Anchorage'), ('overtime', "Overtime")],
                                  string="Type of Entry")
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company)
    employee_ids = fields.Many2many("hr.employee", string="Employees")

    def generate_employee_entries(self):
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError("The End Date must be greater than the Start Date.")

        attendance_domain = [
            ('check_in', '>=', self.start_date),
            ('check_out', '<=', self.end_date),
            ('state', '=', 'validation'), ('is_emp_entry_created', '=', False)
        ]
        timesheet_domain = [('is_emp_entry_created', '=', False),
                            ('date', '>=', self.start_date),
                            ('date', '<=', self.end_date), '|', '|',
                            ('ot_hours', '>', 0.0),
                            ('anchorage', '=', True),
                            ('overseas', '=', True)
                            ]
        if self.employee_ids:
            attendance_domain.append(('employee_id', 'in', self.employee_ids.ids))
            timesheet_domain.append(('employee_id', 'in', self.employee_ids.ids))
        else:
            all_employees = self.env['hr.employee'].search([('active', '=', True)])
            attendance_domain.append(('employee_id', 'in', all_employees.ids))
            timesheet_domain.append(('employee_id', 'in', all_employees.ids))

        attendance_records = self.env['hr.attendance'].sudo().search(attendance_domain)
        self.ot_fixed_allowance(attendance_records)
        timesheets = self.env['account.analytic.line'].search(timesheet_domain)
        self.emp_timesheets_entry(timesheets)

        for emp in timesheets.mapped('employee_id'):
            for entry_type, field_name in [('anchorage_entry', 'anchorage'), ('overseas_entries', 'overseas')]:
                emp_timesheets = timesheets.filtered(
                    lambda t: t.validated_status == 'validated'
                              and t.employee_id.id == emp.id
                              and getattr(t, field_name)
                )
                if emp_timesheets:
                    self.env['hr.employee.entry'].create({
                        'employee_id': emp.id,
                        'type_entry': entry_type,
                        'start_date': self.start_date,
                        'end_date': self.end_date,
                        'duration': len(emp_timesheets),
                        'state': 'draft'
                    })
                    emp_timesheets.write({'is_emp_entry_created': True})

    def ot_fixed_allowance(self, attendance_records):
        if not attendance_records:
            return
        for employee in attendance_records.mapped('employee_id'):
            emp_attendance = attendance_records.filtered(lambda a: a.employee_id == employee)
            overtime_total = sum(emp_attendance.mapped('overtime_hours'))
            over_fixed_amount = employee.contract_id.fixed_allowance
            if overtime_total > 0 and over_fixed_amount > 0 and employee.staff_worker == 'management':
                existing_entry = self.env['hr.employee.entry'].search([
                    ('employee_id', '=', employee.id),
                    ('type_entry', '=', 'overtime_fixed_allowance'),
                    ('start_date', '=', self.start_date),
                    ('end_date', '=', self.end_date),
                    ('state', '=', 'draft'),
                ], limit=1)
                if existing_entry:
                    existing_entry.duration = round(overtime_total, 2)
                else:
                    self.env['hr.employee.entry'].create({
                        'employee_id': employee.id,
                        'type_entry': 'overtime_fixed_allowance',
                        'start_date': self.start_date,
                        'end_date': self.end_date,
                        'duration': round(overtime_total, 2),
                        'state': 'draft',
                        'name': 'OT Allowance for month using Attendance'
                    })

                emp_attendance.write({'is_emp_entry_created': True})
            else:
                emp_attendance.write({'is_emp_entry_created': False})

    def emp_timesheets_entry(self, timesheets):
        """Create or update overtime entries from timesheets, including re-runs after edits."""
        if not timesheets:
            return

        for employee in timesheets.mapped('employee_id'):
            emp_overtime_timesheets = timesheets.filtered(lambda a: a.employee_id == employee)

            # Total OT hours from all timesheets (whether first or edited)
            overtime_total = sum(emp_overtime_timesheets.mapped('ot_hours'))

            # Find or create the overtime entry
            existing_entry = self.env['hr.employee.entry'].search([
                ('employee_id', '=', employee.id),
                ('type_entry', '=', 'overtime'),
                ('start_date', '=', self.start_date),
                ('end_date', '=', self.end_date),
                ('state', '=', 'draft'),
            ], limit=1)

            if overtime_total > 0 and employee.staff_worker == 'technical':
                if existing_entry:
                    # ✅ Update to exact new total (not add again)
                    existing_entry.duration = round(overtime_total, 2)
                else:
                    # ✅ Create new if none exists
                    self.env['hr.employee.entry'].create({
                        'employee_id': employee.id,
                        'type_entry': 'overtime',
                        'start_date': self.start_date,
                        'end_date': self.end_date,
                        'duration': round(overtime_total, 2),
                        'state': 'draft',
                        'name': 'Overtime entry from timesheet',
                    })

                # ✅ Always mark timesheets as processed
                emp_overtime_timesheets.write({'is_emp_entry_created': True})
            else:
                emp_overtime_timesheets.write({'is_emp_entry_created': False})

    # def emp_timesheets_entry(self, timesheets):
    #     if not timesheets:
    #         return
    #     for employee in timesheets.mapped('employee_id'):
    #         print(employee,"employee")
    #         emp_overtime_timesheets = timesheets.filtered(
    #             lambda t: t.validated_status == 'validated' and t.employee_id.id == employee.id and t.ot_hours > 0
    #         )
    #         if emp_overtime_timesheets:
    #             overtime = sum(emp_overtime_timesheets.mapped('ot_hours'))
    #             self.env['hr.employee.entry'].create({
    #                 'employee_id': employee.id,
    #                 'type_entry': 'overtime',
    #                 'start_date': self.start_date,
    #                 'end_date': self.end_date,
    #                 'duration': overtime,
    #                 'state': 'draft',
    #                 # 'name': "This record was generated based on timesheet data."
    #             })
    #             emp_overtime_timesheets.write({'is_emp_entry_created': True})
    #         else:
    #             emp_overtime_timesheets.write({'is_emp_entry_created': False})
