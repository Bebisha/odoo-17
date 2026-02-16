from ast import literal_eval

from odoo import models, fields, api, _
from datetime import date

from odoo.exceptions import ValidationError, UserError


class LeaveEncashment(models.Model):
    _name = "leave.encashment"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Leave Encashment"

    def default_get_paid_leave(self):
        return self.env.ref('hr_holidays.holiday_status_cl').id

    @api.model
    def get_default_employee(self):
        hr_leave_allocation_id = self.env['hr.leave.allocation'].search(
            [('holiday_status_id', '=', self.env.ref('hr_holidays.holiday_status_cl').id)])
        if hr_leave_allocation_id:
            list = []
            for i in hr_leave_allocation_id:
                list.append(i.mapped('employee_id').id)
            return list

    name = fields.Char(string="Reference")
    employee_ids = fields.Many2many('hr.employee', default=get_default_employee)
    employee_id = fields.Many2one("hr.employee", string="Employee")
    leave_type_id = fields.Many2one('hr.leave.type', string="Timeoff Type", default=default_get_paid_leave)
    manager_id = fields.Many2one("hr.employee", string="Manager")
    department_id = fields.Many2one("hr.department", string="Department")
    job_id = fields.Many2one("hr.job", string="Job Position")
    contract_id = fields.Many2one("hr.contract", string="Current Contract")
    approved_date = fields.Date(string="Approved Date", readonly=True)
    allocated_leaves = fields.Integer(string="Allocated Leaves")
    balance_leaves = fields.Integer(string="Balance Leaves")
    paid_leaves = fields.Integer(string="Paid Leaves")
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  default=lambda self: self.env.company.currency_id.id)
    company_id = fields.Many2one(comodel_name='res.company', default=lambda self: self.env.user.company_id,
                                 string='Company')
    gross_per_day = fields.Monetary(string="Gross per day", compute='compute_gross_per_day')
    amount = fields.Monetary(string="Amount", compute='compute_total')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approval', 'Waiting Approval'),
        ('approved', 'Approved'),
        ('reject', 'Rejected'),
        ('cancel', 'Cancelled')
    ], default='draft', tracking=True)

    is_request = fields.Boolean(default=False)
    is_wait_lm_approve = fields.Boolean(default=False)
    is_wait_hrm_approve = fields.Boolean(default=False)
    allocation_id = fields.Many2one("hr.leave.allocation", string="Leave Allocation")

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('leave.encashment.seq')
        vals['is_request'] = True
        return super(LeaveEncashment, self).create(vals)

    @api.onchange('employee_id', 'leave_type_id')
    def get_employee_details(self):
        for rec in self:
            if rec.employee_id:
                leave_encashment_id = self.search(
                    [('employee_id', '=', rec.employee_id.id), ('state', '=', 'approved')])
                if leave_encashment_id:
                    lec_id = leave_encashment_id.filtered(lambda x: x.approved_date.year == date.today().year)
                    if lec_id:
                        raise ValidationError(
                            "Employee %s's Leave Encashment has been already approved" % (rec.employee_id.name))

                rec.manager_id = rec.employee_id.parent_id.id if rec.employee_id.parent_id else False
                rec.department_id = rec.employee_id.department_id.id if rec.employee_id.department_id else False
                rec.job_id = rec.employee_id.job_id.id if rec.employee_id.job_id else False
                contract_id = self.env['hr.contract'].search(
                    [('employee_id', '=', rec.employee_id.id), ('state', '=', 'open')], limit=1)
                rec.contract_id = contract_id.id if contract_id else False

                if rec.leave_type_id:
                    hr_leave_allocation_id = self.env['hr.leave.allocation'].search(
                        [('employee_id', '=', rec.employee_id.id), ('holiday_status_id', '=', rec.leave_type_id.id),
                         ('state', '=', 'validate')])
                    rec.allocated_leaves = sum(hr_leave_allocation_id.mapped('number_of_days'))

                    hr_leave_id = self.env['hr.leave'].search(
                        [('employee_id', '=', rec.employee_id.id), ('holiday_status_id', '=', rec.leave_type_id.id),
                         ('state', '=', 'validate')])
                    rec.balance_leaves = rec.allocated_leaves - sum(hr_leave_id.mapped('number_of_days'))

    @api.depends('employee_id', 'contract_id')
    def compute_gross_per_day(self):
        for rec in self:
            if rec.contract_id and rec.employee_id and rec.contract_id.total_salary:
                rec.gross_per_day = (rec.contract_id.total_salary) / 22
            else:
                rec.gross_per_day = 0.00

    @api.depends('gross_per_day', 'paid_leaves')
    def compute_total(self):
        for rec in self:
            if rec.paid_leaves and rec.gross_per_day:
                rec.amount = rec.gross_per_day * rec.paid_leaves
            else:
                rec.amount = 0.00

    @api.onchange('balance_leaves', 'paid_leaves')
    def check_validity_days(self):
        for rec in self:
            if rec.balance_leaves and rec.paid_leaves:
                if self.paid_leaves > self.balance_leaves:
                    raise ValidationError(_('Paid Leaves must be less than Balance Leaves'))

    def kg_request(self):
        lm_users = []
        if self.balance_leaves <= 0:
            raise ValidationError("Balance Leaves require")

        if self.paid_leaves <= 0:
            raise ValidationError("Paid Leaves require")

        lm_approve_users = self.env['ir.config_parameter'].sudo().get_param(
            'kg_mashirah_oil_purchase.line_manager_ids', False)

        if not lm_approve_users or lm_approve_users == '[]':
            raise ValidationError(_("Please Select Line Manager in Configuration"))

        hrm_approve_users = self.env['ir.config_parameter'].sudo().get_param(
            'kg_mashirah_oil_purchase.hr_manager_ids', False)

        if not hrm_approve_users or hrm_approve_users == '[]':
            raise ValidationError(_("Please Select HR Manager in Configuration"))

        if literal_eval(hrm_approve_users):
            for i in literal_eval(hrm_approve_users):
                users = self.env['res.users'].browse(i)
                if users:
                    lm_users.append(users)

            for user in lm_users:
                self.activity_schedule('kg_mashirah_oil_hrms.line_manager_approval_notification',
                                       user_id=user.id,
                                       note=f' The User {self.env.user.name} request the Line Manager to approve the Leave Encashment {self.name}. Please Verify and approve.')

        self.is_wait_lm_approve = True
        self.state = 'waiting_approval'

    def kg_lm_approve(self):
        lm_users = []
        lm_approve_users = self.env['ir.config_parameter'].sudo().get_param(
            'kg_mashirah_oil_purchase.line_manager_ids', False)

        if self.env.user.id not in literal_eval(lm_approve_users):
            raise ValidationError(_("You have no access to approve"))

        else:
            lm_manager_notification_activity = self.env.ref(
                'kg_mashirah_oil_hrms.line_manager_approval_notification')

            activity_1 = self.activity_ids.filtered(
                lambda l: l.activity_type_id == lm_manager_notification_activity)
            not_current_user_confirm = activity_1.filtered(lambda l: l.user_id != self.env.user)

            for ccc in not_current_user_confirm:
                ccc.unlink()

            activity_2 = self.activity_ids.filtered(
                lambda l: l.activity_type_id == lm_manager_notification_activity)
            activity_2.action_done()

            if literal_eval(lm_approve_users):
                for i in literal_eval(lm_approve_users):
                    users = self.env['res.users'].browse(i)
                    if users:
                        lm_users.append(users)

                for user in lm_users:
                    self.activity_schedule('kg_mashirah_oil_hrms.hr_manager_approval_notification',
                                           user_id=user.id,
                                           note=f' The user {self.env.user.name} has approved the Line Manager approval and request the HR Manager to approve the Leave Encashment {self.name}. Please Verify and approve.')

            self.is_wait_hrm_approve = True

    def kg_hrm_approve(self):
        hrm_users = []
        hrm_approve_users = self.env['ir.config_parameter'].sudo().get_param(
            'kg_mashirah_oil_purchase.hr_manager_ids', False)

        if self.env.user.id not in literal_eval(hrm_approve_users):
            raise ValidationError(_("You have no access to approve"))

        else:
            hrm_manager_notification_activity = self.env.ref(
                'kg_mashirah_oil_hrms.hr_manager_approval_notification')

            activity_1 = self.activity_ids.filtered(
                lambda l: l.activity_type_id == hrm_manager_notification_activity)
            not_current_user_confirm = activity_1.filtered(lambda l: l.user_id != self.env.user)

            for ccc in not_current_user_confirm:
                ccc.unlink()

            activity_2 = self.activity_ids.filtered(
                lambda l: l.activity_type_id == hrm_manager_notification_activity)
            activity_2.action_done()

            if literal_eval(hrm_approve_users):
                for i in literal_eval(hrm_approve_users):
                    users = self.env['res.users'].browse(i)
                    if users:
                        hrm_users.append(users)


                for user in hrm_users:
                    self.activity_schedule('kg_mashirah_oil_hrms.leave_encashment_approval_notification',
                                           user_id=user.id,
                                           note=f' The user {self.env.user.name} has approved the HR Manager approval of the Leave Encashment {self.name}.')

            self.state = 'approved'
            self.approved_date = date.today()

            hrm_notification_activity = self.env.ref(
                'kg_mashirah_oil_hrms.leave_encashment_approval_notification')

            activity_1 = self.activity_ids.filtered(
                lambda l: l.activity_type_id == hrm_notification_activity)
            not_current_user_confirm = activity_1.filtered(lambda l: l.user_id != self.env.user)

            for ccc in not_current_user_confirm:
                ccc.unlink()

            activity_2 = self.activity_ids.filtered(
                lambda l: l.activity_type_id == hrm_notification_activity)
            activity_2.action_done()

            hr_leave_allocation_id = self.env['hr.leave.allocation'].search(
                [('employee_id', '=', self.employee_id.id), ('state', '=', 'validate'),
                 ('holiday_status_id', '=', self.leave_type_id.id)], limit=1)
            hr_leave_allocation_id.action_refuse()
            data = {
                'name': 'Paid Timeoff %s (Leave Encashment)' % (date.today().year),
                'holiday_status_id': self.leave_type_id.id,
                'date_from': hr_leave_allocation_id.date_from,
                'allocation_type': 'regular',
                'employee_id': self.employee_id.id,
                'number_of_days': self.balance_leaves - self.paid_leaves
            }
            allocation = self.env['hr.leave.allocation'].create(data)
            allocation.action_validate()
            self.allocation_id = allocation.id

    def kg_reject(self):
        if not self.is_wait_hrm_approve:
            lm_approve_users = self.env['ir.config_parameter'].sudo().get_param(
                'kg_mashirah_oil_purchase.line_manager_ids', False)

            if self.env.user.id not in literal_eval(lm_approve_users):
                raise ValidationError(_("You have no access to reject"))

        else:
            hrm_approve_users = self.env['ir.config_parameter'].sudo().get_param(
                'kg_mashirah_oil_purchase.hr_manager_ids', False)

            if self.env.user.id not in literal_eval(hrm_approve_users):
                raise ValidationError(_("You have no access to reject"))

        self.activity_schedule('kg_mashirah_oil_hrms.reject_leave_encashment_notification',
                               user_id=self.create_uid.id,
                               note=f' The user {self.env.user.name}  has rejected the approval of the Leave Encashment {self.name}.')

        reject_lec_notification_activity = self.env.ref(
            'kg_mashirah_oil_hrms.reject_leave_encashment_notification')
        activity = self.activity_ids.filtered(
            lambda l: l.activity_type_id == reject_lec_notification_activity)
        activity.action_done()

        hr_manager_notification_activity = self.env.ref(
            'kg_mashirah_oil_hrms.hr_manager_approval_notification')
        activity_1 = self.activity_ids.filtered(lambda l: l.activity_type_id == hr_manager_notification_activity)
        activity_1.unlink()

        line_manager_notification_activity = self.env.ref(
            'kg_mashirah_oil_hrms.line_manager_approval_notification')
        activity_1 = self.activity_ids.filtered(lambda l: l.activity_type_id == line_manager_notification_activity)
        activity_1.unlink()

        self.state = 'reject'
        self.is_wait_lm_approve = False
        self.is_wait_hrm_approve = False
        self.is_request = False

    def kg_cancel(self):
        self.state = 'cancel'
        self.is_wait_lm_approve = False
        self.is_wait_hrm_approve = False
        self.is_request = False

    def kg_action_draft(self):
        self.state = 'draft'
        self.is_wait_lm_approve = False
        self.is_wait_hrm_approve = False
        self.is_request = True

    def unlink(self):
        for rec in self:
            if rec.state not in ('draft'):
                raise UserError(_('You cannot delete a record which is not in draft state'))
        return super(LeaveEncashment, self).unlink()
