from odoo import models, fields, api


class HrLeaveAllocation(models.Model):
    _inherit = 'hr.leave.allocation'
    _description = 'hr.leave.allocation'

    is_negative_allocation = fields.Boolean(string='Is Negative Leave Allocation?')
    is_deducted = fields.Boolean(string='Is Balance Deducted?')

    @api.depends('holiday_status_id', 'employee_id')
    @api.constrains('holiday_status_id', 'employee_id')
    def _negative_balance_deduction(self):
        """ To reduce the negative balance from previous allocation """
        if not self.is_negative_allocation:
            if self.holiday_status_id.annual_leave:
                if self.employee_id.negative_leave:
                    self.number_of_days = self.number_of_days - float(self.employee_id.negative_leave)

    def action_validate(self):
        """ Inherited to add condition to mark leave deduction and resetting employee negative leave """
        res = super(HrLeaveAllocation, self).action_validate()

        hr_leave_allocation_id = self.env['hr.leave.allocation'].search(
            [('employee_id', '=', self.employee_id.id), ('is_negative_allocation', '=', True),
             ('is_deducted', '=', False),
             ('holiday_status_id', '=', self.holiday_status_id.id), ('state', '=', 'validate')]
        )

        for rec in hr_leave_allocation_id:
            rec.is_deducted = True

        if self.employee_id.negative_leave:
            self.employee_id.negative_leave = False

        return res
