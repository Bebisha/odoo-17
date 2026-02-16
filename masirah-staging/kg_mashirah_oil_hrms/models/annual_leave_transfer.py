from ast import literal_eval
from datetime import date

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class AnnualLeaveTransfer(models.Model):
    _name = "annual.leave.transfer"
    _description = "Annual Leave Transfer"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def default_get_annual_leave(self):
        return self.env.ref('hr_holidays.holiday_status_cl').id

    name = fields.Char(string="Reference")
    employee_id = fields.Many2one("hr.employee", string="Employee")
    leave_type_id = fields.Many2one('hr.leave.type', string="Timeoff Type", default=default_get_annual_leave)
    allocated_leaves = fields.Integer(string="Allocated Leaves")
    balance_leaves = fields.Integer(string="Balance Leaves")
    transfer_leaves = fields.Integer(string="Transfer Leaves")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approval', 'Waiting Approval'),
        ('approved', 'Approved'),
        ('reject', 'Rejected'),
        ('cancel', 'Cancelled')], default='draft', tracking=True)

    is_request = fields.Boolean(default=False)
    is_wait_hrm = fields.Boolean(default=False)
    is_approved = fields.Boolean(default=False)
    is_rejected = fields.Boolean(default=False)

    validity_date_from = fields.Date("Date From")
    validity_date_to = fields.Date("Date To")
    allocation_id = fields.Many2one('hr.leave.allocation')
    transfer_date = fields.Date(string="Transfer Date", default=date.today())

    @api.model
    def create(self, vals):
        emp_id = self.env['hr.employee'].search([('id', '=', vals['employee_id'])])
        vals['name'] = str(emp_id.name) + '-' + str(date.today().year) + '-' + self.env[
            'ir.sequence'].next_by_code(
            'annual.transfer.seq')
        vals['is_request'] = True
        return super(AnnualLeaveTransfer, self).create(vals)

    @api.onchange('balance_leaves', 'transfer_leaves')
    def check_validity_days(self):
        for rec in self:
            if rec.balance_leaves and rec.transfer_leaves:
                if self.transfer_leaves > self.balance_leaves:
                    raise ValidationError(_('Transfer Leaves must be less than Balance Leaves'))

    @api.onchange('validity_date_from', 'validity_date_to')
    def check_validity_dates(self):
        for rec in self:
            if rec.validity_date_to and rec.validity_date_from:
                if self.validity_date_from > self.validity_date_to:
                    raise ValidationError(_('Validity Start Date must be less than Validity End Date'))

    @api.onchange('employee_id')
    def check_balance_leaves(self):
        for rec in self:
            if rec.employee_id:
                annual_transfer_id = self.search([('employee_id', '=', rec.employee_id.id), ('state', '=', 'approved')])
                if annual_transfer_id:
                    ant_id = annual_transfer_id.filtered(lambda x: x.transfer_date.year == date.today().year)
                    if ant_id:
                        raise ValidationError(
                            "Employee %s's annual leave has been already transferred" % (rec.employee_id.name))

                hr_leave_allocation_id = self.env['hr.leave.allocation'].search(
                    [('employee_id', '=', rec.employee_id.id), ('holiday_status_id', '=', rec.leave_type_id.id),
                     ('state', '=', 'validate')])
                rec.allocated_leaves = sum(hr_leave_allocation_id.mapped('number_of_days'))
                hr_leave_id = self.env['hr.leave'].search(
                    [('employee_id', '=', rec.employee_id.id), ('holiday_status_id', '=', rec.leave_type_id.id),
                     ('state', '=', 'validate')])
                rec.balance_leaves = rec.allocated_leaves - sum(hr_leave_id.mapped('number_of_days'))

    def kg_request(self):
        if self.transfer_leaves <= 0:
            raise ValidationError("Transfer Leaves require")

        hrm_users = []
        hrm_approve_users = self.env['ir.config_parameter'].sudo().get_param(
            'kg_mashirah_oil_purchase.hr_manager_ids', False)

        if not hrm_approve_users or hrm_approve_users == '[]':
            raise ValidationError(_("Please Select HR Manager in Configuration"))

        if literal_eval(hrm_approve_users):
            for i in literal_eval(hrm_approve_users):
                users = self.env['res.users'].browse(i)
                if users:
                    hrm_users.append(users)

            for user in hrm_users:
                self.activity_schedule('kg_mashirah_oil_hrms.hr_manager_approval_notification',
                                       user_id=user.id,
                                       note=f' The User {self.env.user.name} request the HR Manager to approve the Annual Leave Transfer {self.name}. Please Verify and approve.')

        self.state = 'waiting_approval'
        self.is_wait_hrm = True

    def kg_hrm_approve(self):
        hm_users = []
        hrm_approve_users = self.env['ir.config_parameter'].sudo().get_param(
            'kg_mashirah_oil_purchase.hr_manager_ids', False)

        if self.env.user.id not in literal_eval(hrm_approve_users):
            raise ValidationError(_("You have no access to approve"))

        else:
            hr_manager_notification_activity = self.env.ref(
                'kg_mashirah_oil_hrms.hr_manager_approval_notification')

            activity_1 = self.activity_ids.filtered(
                lambda l: l.activity_type_id == hr_manager_notification_activity)
            not_current_user_confirm = activity_1.filtered(lambda l: l.user_id != self.env.user)

            for ccc in not_current_user_confirm:
                ccc.unlink()

            activity_2 = self.activity_ids.filtered(
                lambda l: l.activity_type_id == hr_manager_notification_activity)
            activity_2.action_done()

            if literal_eval(hrm_approve_users):
                for i in literal_eval(hrm_approve_users):
                    users = self.env['res.users'].browse(i)
                    if users:
                        hm_users.append(users)

                for user in hm_users:
                    self.activity_schedule('kg_mashirah_oil_hrms.annual_transfer_approval_notification',
                                           user_id=user.id,
                                           note=f' The user {self.env.user.name} has approved the HR Manager approval of the Annual Leave Transfer {self.name}.')

            self.state = 'approved'
            self.is_approved = True
            vals = {
                'name': 'Annual Leave %s (Carry forwarded)' % (date.today().year),
                'holiday_status_id': self.leave_type_id.id,
                'date_from': self.validity_date_from,
                'date_to': self.validity_date_to,
                'allocation_type': 'regular',
                'employee_id': self.employee_id.id,
                'number_of_days': self.transfer_leaves
            }
            allocation = self.env['hr.leave.allocation'].create(vals)
            allocation.action_validate()
            self.allocation_id = allocation.id

            hrm_notification_activity = self.env.ref(
                'kg_mashirah_oil_hrms.annual_transfer_approval_notification')

            activity_1 = self.activity_ids.filtered(
                lambda l: l.activity_type_id == hrm_notification_activity)
            not_current_user_confirm = activity_1.filtered(lambda l: l.user_id != self.env.user)

            for ccc in not_current_user_confirm:
                ccc.unlink()

            activity_2 = self.activity_ids.filtered(
                lambda l: l.activity_type_id == hrm_notification_activity)
            activity_2.action_done()

    def kg_reject(self):
        hrm_approve_users = self.env['ir.config_parameter'].sudo().get_param(
            'kg_mashirah_oil_purchase.hr_manager_ids', False)

        if self.env.user.id not in literal_eval(hrm_approve_users):
            raise ValidationError(_("You have no access to reject"))

        self.activity_schedule('kg_mashirah_oil_hrms.reject_annual_leave_transfer_notification',
                               user_id=self.create_uid.id,
                               note=f' The user {self.env.user.name}  has rejected the approval of the Annual Leave Transfer {self.name}.')

        reject_amlt_notification_activity = self.env.ref(
            'kg_mashirah_oil_hrms.reject_annual_leave_transfer_notification')
        activity = self.activity_ids.filtered(
            lambda l: l.activity_type_id == reject_amlt_notification_activity)
        activity.action_done()

        hr_manager_notification_activity = self.env.ref(
            'kg_mashirah_oil_hrms.hr_manager_approval_notification')
        activity_1 = self.activity_ids.filtered(lambda l: l.activity_type_id == hr_manager_notification_activity)
        activity_1.unlink()

        self.state = 'reject'
        self.is_rejected = True

    def action_view_allocations(self):
        return {
            'name': 'Leave Allocations',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'hr.leave.allocation',
            'domain': [('id', '=', self.allocation_id.id)],
            'target': 'current'
        }

    def unlink(self):
        for rec in self:
            if rec.state not in ('draft'):
                raise UserError(_('You cannot delete a record which is not in draft state'))
        return super(AnnualLeaveTransfer, self).unlink()
