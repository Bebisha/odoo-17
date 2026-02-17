from odoo import models, fields, api, _


class LeaveSettlement(models.Model):
    _name = 'leave.settlement'
    _description = 'Leave Settlement'

    name = fields.Char(string='Reference', default=lambda self: _('New'), readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)
    department_id = fields.Many2one('hr.department', string='Department', related="employee_id.department_id")
    emp_registration_number = fields.Char("Employee No.", related="employee_id.employee_no")
    emp_job_title = fields.Char("Designation", related="employee_id.job_title")
    balance_leave = fields.Float(string="Leave Balance")
    leave_total = fields.Float(string="Total Leaves")
    leaves_taken = fields.Float(string="Leaves Taken")
    holiday_status_id = fields.Many2one("hr.leave.type", string="Time Off Type")
    # , domain = "[('annual_leave', '=', True)]"
    leave_ids = fields.Many2many('hr.leave', string='Leaves')
    leave_allowances_ids = fields.One2many('leave.allowance', 'leave_settlement_id', string='Other Allowances')
    state = fields.Selection(selection=[('draft', 'Draft'),
                                        ('paid', 'Paid')],
                             default='draft', string='State')
    leave_pay = fields.Float(string='Leave Pay')
    amount_to_pay = fields.Float(string='Total Amount')
    days = fields.Integer(string='No. of Days')

    def action_pay(self):
        self.state = 'paid'
        if self.leave_ids:
            for rec in self.leave_ids:
                rec.paid = True

    def action_set_draft(self):
        self.state = 'draft'
        if self.leave_ids:
            for rec in self.leave_ids:
                rec.paid = False

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'leave.settlement.sequence') or _('New')
        return super(LeaveSettlement, self).create(vals)

    @api.onchange('holiday_status_id')
    def _onchange_holiday_status_id(self):
        if self.holiday_status_id:
            self.leave_ids = False
            return {
                'domain': {
                    'leave_ids': [
                        ('holiday_status_id', '=', self.holiday_status_id.id)
                    ]
                }
            }
        else:
            return {
                'domain': {}
            }

    @api.depends('employee_id', 'holiday_status_id', 'leave_ids')
    @api.onchange('employee_id', 'holiday_status_id', 'leave_ids')
    def _onchange_employee(self):
        """ To compute total leave, taken leave and balance leaves based on employee and leave type  """
        for rec in self:
            rec.balance_leave = False
            rec.leaves_taken = False
            rec.leave_total = False
            if rec.holiday_status_id:
                for leave in rec.leave_ids:
                    if rec.employee_id != leave.employee_id:
                        rec.leave_ids = False
                hr_leave_allocation_id = self.env['hr.leave.allocation'].search(
                    [('employee_id', '=', rec.employee_id.id),
                     ('holiday_status_id', '=', rec.holiday_status_id.id), ('state', '=', 'validate')])

                hr_leave_id = self.env['hr.leave'].search(
                    [('employee_id', '=', rec.employee_id.id), ('holiday_status_id', '=', rec.holiday_status_id.id),
                     ('state', '=', 'validate')])

                if rec.leave_ids:
                    rec.leave_total = sum(hr_leave_allocation_id.mapped('number_of_days'))
                    rec.balance_leave = rec.leave_total - sum(hr_leave_id.mapped('number_of_days'))
                    rec.leaves_taken = rec.leave_total - rec.balance_leave

    @api.depends('leaves_taken', 'employee_id', 'holiday_status_id', 'leave_ids', 'leave_allowances_ids')
    @api.onchange('leaves_taken', 'employee_id', 'holiday_status_id', 'leave_ids', 'leave_allowances_ids')
    def _onchange_leaves_taken(self):
        """ To calculate leave pay, other allowance amount and total amount based on employee, leave type and allowances """
        for rec in self:
            amount = rec.employee_id.contract_id.wage + rec.employee_id.contract_id.housing_allowance + rec.employee_id.contract_id.travel_allowance + rec.employee_id.contract_id.other_allowance + rec.employee_id.contract_id.extra_income
            per_day = amount / 30
            total_alw_amount = 0
            for line in self.leave_allowances_ids:
                line.amount = per_day * line.days
                total_alw_amount += line.amount
            rec.leave_pay = per_day * rec.leaves_taken
            rec.amount_to_pay = per_day * rec.leaves_taken + total_alw_amount
