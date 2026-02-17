from odoo import models, fields, api


class LeaveAllowance(models.Model):
    _name = 'leave.allowance'
    _description = 'Leave Allowances'

    name = fields.Char(string='Label')
    days = fields.Integer(string='No. Of Days')
    amount = fields.Float(string='Amount')
    old_contract = fields.Boolean(string='Old Contract')
    leave_settlement_id = fields.Many2one('leave.settlement', 'Leave Settlement')

    @api.depends('days')
    @api.onchange('days')
    def _onchange_days(self):
        """ To calculate the amount based on number of days """
        if self.days and self.leave_settlement_id:
            amount = self.leave_settlement_id.employee_id.contract_id.wage + self.leave_settlement_id.employee_id.contract_id.housing_allowance + self.leave_settlement_id.employee_id.contract_id.travel_allowance + self.leave_settlement_id.employee_id.contract_id.other_allowance + self.leave_settlement_id.employee_id.contract_id.extra_income
            per_day = amount / 30
            self.amount = per_day * self.days

