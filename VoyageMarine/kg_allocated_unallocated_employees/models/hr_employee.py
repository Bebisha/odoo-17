from odoo import fields, models


class AllocatedUnallocatedEmployees(models.Model):
    _inherit = "hr.employee"

    availability_status = fields.Selection([('available', 'Available')], compute="compute_is_employee_available")

    def compute_is_employee_available(self):
        for rec in self:
            rec.availability_status = False
            if rec.staff_worker == 'technical':
                timesheet_ids = self.env['account.analytic.line'].search(
                    [('date', '=', fields.Date.today()), ('employee_id', '=', rec.id)], limit=1)
                if not timesheet_ids:
                    rec.availability_status = 'available'
