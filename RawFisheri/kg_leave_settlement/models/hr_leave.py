from odoo import models, fields, api


class HrLeave(models.Model):
    _inherit = 'hr.leave'
    _description = 'HR Leave'

    paid = fields.Boolean('Paid')


class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'
    _description = 'HR Leave Type'

    annual_leave = fields.Boolean('Is Annual Leave?')
