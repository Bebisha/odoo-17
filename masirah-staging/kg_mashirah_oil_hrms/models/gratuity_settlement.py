from odoo import models, fields, api, _, exceptions
from odoo.exceptions import ValidationError


class GratuitySettlement(models.Model):
    _name = "gratuity.settlement"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Gratuity Settlement"
    _rec_name = 'sequence_num'

    sequence_num = fields.Char(string='Number', readonly=True, default=lambda self: _('New'))

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)


    current_contract = fields.Many2one('hr.contract', string='Contract')
    join_date = fields.Date(string="Date Of Join")
    manager_new_id = fields.Many2one('hr.employee', string="Manager")
    basic_salary_wage = fields.Many2one('hr.contract', string="Salary")
    wage = fields.Float(string="Salary")
    department_id = fields.Many2one('hr.department', string='Department')
    releiving_date = fields.Date(string="Relieving Date")
    total_days_worked = fields.Integer(string='Total Days Worked', compute='_compute_total_days')
    service_year = fields.Integer(string="Year Of Service", compute='compute_service')
    amount_gratuity = fields.Float(string="Gratuity Amount", compute="compute_gratuity_amount")
    unpaid_days = fields.Integer(string="Gratuity Eligible Days", compute="compute_unpaid_daysss")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('done', 'Done'),
        ('cancel', 'Cancel')], default='draft')

    def create(self, vals):
        if vals.get('sequence_num', _('New')) == _('New'):
            vals['sequence_num'] = self.env['ir.sequence'].next_by_code(
                'gratuity.settlement') or _('New')
        seq_num = super(GratuitySettlement, self).create(vals)
        return seq_num

    def action_confirm(self):
        for record in self:
            if self.search_count([('employee_id', '=', record.employee_id.id)]) > 1:
                raise exceptions.ValidationError("An employee can have only one Gratuity Record.")

        if self.join_date > self.releiving_date:
            raise ValidationError(_('Joining Date must be less than Relieving Date'))
        self.write({
            'state': 'confirm'

        })



    def action_done(self):
        self.write({
            'state': 'done'
        })

    def action_cancel(self):
        self.write({
            'state': 'cancel'
        })

    def action_reset(self):
        self.write({
            'state': 'draft'
        })

    @api.onchange('employee_id')
    def onchange_employee(self):
        if self.employee_id:
            self.department_id = self.employee_id.department_id.id
            self.join_date = self.employee_id.date_of_join
            self.manager_new_id = self.employee_id.parent_id.id
            self.current_contract = next(
                (contract.id for contract in self.employee_id.contract_ids if contract.state == 'open'), None)

            self.wage = self.current_contract.wage

    @api.depends('join_date', 'releiving_date')
    def compute_service(self):
        for rec in self:
            rec.service_year = False
            if rec.releiving_date:
                delta = self.releiving_date - self.join_date
                date = delta.days // 365
                rec.service_year = date

    # @api.depends('join_date', 'releiving_date')
    # def compute_service(self):
    #     # date = False
    #     service_year=False
    #     if self.releiving_date:
    #         delta = self.releiving_date - self.join_date
    #         date = delta.days // 365
    #         self.service_year = date

    @api.depends('wage', 'service_year')
    def compute_gratuity_amount(self):
        for employee in self:
            if employee.service_year >= 3:
                employee.amount_gratuity = (employee.wage / 30) * 30 * employee.service_year

            else:
                employee.amount_gratuity = (employee.wage / 30) * 15 * employee.service_year

    @api.depends('join_date', 'releiving_date')
    def _compute_total_days(self):
        for employee in self:
            if employee.join_date and employee.releiving_date:
                delta = employee.releiving_date - employee.join_date
                employee.total_days_worked = delta.days + 1
            else:
                employee.total_days_worked = 0

    @api.depends('total_days_worked')
    def compute_unpaid_daysss(self):
        for employee in self:
            self.unpaid_days = False
            leave_deduc = self.env['hr.leave'].search([('employee_id', '=', employee.id), (
            'holiday_status_id', '=', self.env.ref('hr_holidays.holiday_status_unpaid').id),
                                                       ('state', '=', 'validate')])
            total_unpaid = sum(leave_deduc.mapped('number_of_days_display'))
            employee.total_days_worked -= total_unpaid
            self.unpaid_days = employee.total_days_worked
