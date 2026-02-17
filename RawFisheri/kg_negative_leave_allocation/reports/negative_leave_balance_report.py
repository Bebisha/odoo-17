from odoo import models, fields, api


class NegativeLeaveBalance(models.Model):
    _name = 'negative.leave.balance.report'
    _description = 'Negative Leave Balance Report'

    employee_id = fields.Many2one('hr.employee', 'Employee')
    employee_no = fields.Char(string='Employee Number')
    department_id = fields.Many2one('hr.department', string='Department', readonly=True)
    country_id = fields.Many2one('res.country', string='Nationality', readonly=True)
    job_id = fields.Many2one('hr.job', string='Job', readonly=True)
    leave_type_id = fields.Many2one('hr.leave.type', string='Leave Type', readonly=True)
    # allocated_days = fields.Integer('Accrued Leave')
    # taken_days = fields.Integer('Taken Leaves')
    balance_days = fields.Float('Negative Balance')
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company)

    def negative_leave_balance(self):
        """ To view the negative leave balance report """
        records = self.env['negative.leave.balance.report'].search([])
        records.unlink()
        employees = self.env['hr.employee'].search([('has_negative_leave', '=', True)])
        for employee in employees:
            leave_allocation_id = self.env['hr.leave.allocation'].search(
                [('employee_id', '=', employee.id), ('is_negative_allocation', '=', True), ('is_deducted', '=', False)]
            )

            vals = {
                'employee_id': employee.id,
                'employee_no': employee.employee_no,
                'department_id': employee.department_id.id,
                'job_id': employee.job_id.id,
                'country_id': employee.country_id.id,
                'balance_days': employee.negative_leave,
                'leave_type_id': leave_allocation_id.holiday_status_id.id
            }

            self.env['negative.leave.balance.report'].create(vals)

        return {
            'name': 'Negative Leave Balance Report',
            'view_mode': 'tree',
            'res_model': 'negative.leave.balance.report',
            'type': 'ir.actions.act_window',
            'context': {},
            'target': 'main'
        }

    def negative_leave_balance_pdf(self):
        """ PDF report for negative leave balance """
        values = []
        for rec in self:
            vals = {
                'employee': rec.employee_id.name,
                'department': rec.department_id.name,
                'job': rec.job_id.name,
                'leave_type': rec.leave_type_id.name,
                'balance_days': rec.balance_days
            }
            values.append(vals)

        data = {
            'company_id': self.company_id.name,
            'value_list': values,
        }

        return self.env.ref('kg_negative_leave_allocation.action_report_negative_leave_balance_pdf').with_context(
            landscape=True).report_action(self, data=data)
