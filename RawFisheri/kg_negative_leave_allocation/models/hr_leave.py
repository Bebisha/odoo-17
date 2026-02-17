from datetime import date

from odoo import models, fields


class HrLeave(models.Model):
    _inherit = 'hr.leave'
    _description = 'hr.leave'

    def _check_validity(self):
        """ Adding the functionality for allowing negative leave for annual leaves """
        if self.holiday_status_id.annual_leave:
            hr_leave_allocation_id = self.env['hr.leave.allocation'].search(
                [('employee_id', '=', self.employee_id.id),
                 ('holiday_status_id', '=', self.holiday_status_id.id), ('state', '=', 'validate')])

            hr_leave_id = self.env['hr.leave'].search(
                [('employee_id', '=', self.employee_id.id), ('holiday_status_id', '=', self.holiday_status_id.id),
                 ('state', '=', 'validate')])

            leave_total = sum(hr_leave_allocation_id.mapped('number_of_days'))
            balance_leave = leave_total - sum(hr_leave_id.mapped('number_of_days')) - self.number_of_days

            data = {
                'name': 'Paid Timeoff %s (Negative Leave Balance)' % (date.today().year),
                'holiday_status_id': self.holiday_status_id.id,
                'date_from': date.today(),
                'allocation_type': 'regular',
                'is_negative_allocation': True,
                'employee_id': self.employee_id.id,
                'number_of_days': abs(balance_leave)
            }

            self.employee_id.has_negative_leave = True
            balance = float(self.employee_id.negative_leave) + abs(balance_leave)
            self.employee_id.negative_leave = balance
            allocation = self.env['hr.leave.allocation'].create(data)
            allocation.sudo().action_validate()

        return super(HrLeave, self)._check_validity()
