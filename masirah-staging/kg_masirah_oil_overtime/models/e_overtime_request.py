# -*- coding: utf-8 -*-
######################################################################################
#
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the Software
#    or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
########################################################################################
from ast import literal_eval
from datetime import datetime

from dateutil import relativedelta
import pandas as pd
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.resource.models.utils import HOURS_PER_DAY


class HrOverTime(models.Model):
    _name = 'hr.overtime'
    _description = "HR Overtime"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _get_employee_domain(self):
        employee = self.env['hr.employee'].search(
            [('user_id', '=', self.env.user.id)], limit=1)
        domain = [('id', '=', employee.id)]
        if self.env.user.has_group('hr.group_hr_user'):
            domain = []
        return domain

    def _default_employee(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    @api.onchange('days_no_tmp')
    def _onchange_days_no_tmp(self):
        self.days_no = self.days_no_tmp

    @api.depends('employee_id')
    def get_logged_user(self):
        for rec in self:
            rec.employee_id = rec.env.user.id

    name = fields.Char('Name', readonly=True)
    is_overtime = fields.Boolean(string="Hr Over")
    employee_id = fields.Many2one('hr.employee', string='Employee',
                                  domain=_get_employee_domain, default=lambda self: self.env.user.employee_id.id,
                                  store=True, compute="get_logged_user",
                                  required=True)
    department_id = fields.Many2one('hr.department', string="Department",
                                    related="employee_id.department_id")
    job_id = fields.Many2one('hr.job', string="Job", related="employee_id.job_id")
    manager_id = fields.Many2one('res.users', string="Manager",
                                 related="employee_id.parent_id.user_id", store=True)
    current_user = fields.Many2one('res.users', string="Current User",
                                   related='employee_id.user_id',
                                   default=lambda self: self.env.uid,
                                   store=True)
    current_user_boolean = fields.Boolean()
    project_id = fields.Many2one('project.project', string="Project")
    project_manager_id = fields.Many2one('res.users', string="Project Manager")
    contract_id = fields.Many2one('hr.contract', string="Contract",
                                  related="employee_id.contract_id",
                                  )
    date_from = fields.Datetime('Date From')
    date_to = fields.Datetime('Date to')
    days_no_tmp = fields.Float('Hours', compute="_get_days", store=True)
    days_no = fields.Float('No. of Days', store=True)
    desc = fields.Text('Description')
    state = fields.Selection([('draft', 'Draft'),
                              ('f_approve', 'Waiting'),
                              ('approved', 'Approved'),
                              ('cancel', 'Cancelled'),
                              ('refused', 'Rejected')], string="State",
                             default="draft")
    cancel_reason = fields.Text('Refuse Reason')
    leave_id = fields.Many2one('hr.leave.allocation',
                               string="Leave Allocation")
    attchd_copy = fields.Binary('Attach A File')
    attchd_copy_name = fields.Char('File Name')
    type = fields.Selection([('cash', 'Cash'), ('leave', 'leave')], default="leave", required=True, string="Type")
    overtime_type_id = fields.Many2one('overtime.type',
                                       domain="[('type','=',type),('duration_type','='," "duration_type)]")
    public_holiday = fields.Char(string='Public Holiday', readonly=True)
    attendance_ids = fields.Many2many('hr.attendance', string='Attendance')
    work_schedule = fields.One2many(
        related='employee_id.resource_calendar_id.attendance_ids')
    global_leaves = fields.One2many(
        related='employee_id.resource_calendar_id.global_leave_ids')
    duration_type = fields.Selection([('hours', 'Hour'), ('days', 'Days')], string="Duration Type", default="hours",
                                     required=True)
    cash_hrs_amount = fields.Float(string='Overtime Amount', readonly=True)
    cash_day_amount = fields.Float(string='Overtime Amount', readonly=True)
    payslip_paid = fields.Boolean('Paid in Payslip', readonly=True)
    shift_type = fields.Selection(
        [('day', 'Day'), ('night', 'Night'), ('restday_public_holiday', 'Restday/Public Holiday')], default="day",
        required=True, string="Shift Type")
    overtime_amount = fields.Float(string="Overtime Amount", compute="compute_overtime_amount")
    over_time_day = fields.Selection(
        [('week_day', 'Week Days'), ('weekend', 'Weekend'), ('public_holidays', 'Public Holidays')],
        string="OverTime Days", default='week_day')
    work_entry_id = fields.Many2one("hr.work.entry", string="Work Entry")
    is_lm_approved = fields.Boolean(default=False, copy=False)
    is_hr = fields.Boolean(compute='compute_is_hr', copy=False)
    is_hr_approved = fields.Boolean(default=False, copy=False)
    is_request = fields.Boolean(default=False, copy=False)

    @api.depends('employee_id')
    def compute_is_hr(self):
        if not self.env.user.has_group('hr.group_hr_manager'):
            self.is_hr = True
        else:
            self.is_hr = False

    @api.depends('shift_type', 'contract_id', 'days_no_tmp')
    def compute_overtime_amount(self):
        for rec in self:
            if rec.type == 'cash':
                if rec.shift_type == 'day':
                    rec.overtime_amount = rec.contract_id.over_hour * 1.25 * rec.days_no_tmp
                elif rec.shift_type == 'night':
                    rec.overtime_amount = rec.contract_id.over_hour * 1.5 * rec.days_no_tmp
                else:
                    rec.overtime_amount = rec.contract_id.over_hour * 2.0 * rec.days_no_tmp
            else:
                rec.overtime_amount = 0.00

    @api.onchange('employee_id')
    def _get_defaults(self):
        for sheet in self:
            if sheet.employee_id:
                sheet.update({
                    'department_id': sheet.employee_id.department_id.id,
                    'job_id': sheet.employee_id.job_id.id,
                    'manager_id': sheet.sudo().employee_id.parent_id.user_id.id,
                })

    @api.depends('project_id')
    def _get_project_manager(self):
        for sheet in self:
            if sheet.project_id:
                sheet.update({
                    'project_manager_id': sheet.project_id.user_id.id,
                })

    @api.depends('date_from', 'date_to')
    def _get_days(self):
        for recd in self:
            if recd.date_from and recd.date_to:
                if recd.date_from > recd.date_to:
                    raise ValidationError('Start Date must be less than End Date')
        for sheet in self:
            if sheet.date_from and sheet.date_to:
                start_dt = fields.Datetime.from_string(sheet.date_from)
                finish_dt = fields.Datetime.from_string(sheet.date_to)
                s = finish_dt - start_dt
                difference = relativedelta.relativedelta(finish_dt, start_dt)
                hours = difference.hours
                minutes = difference.minutes
                days_in_mins = s.days * 24 * 60
                hours_in_mins = hours * 60
                days_no = ((days_in_mins + hours_in_mins + minutes) / (24 * 60))

                diff = sheet.date_to - sheet.date_from
                days, seconds = diff.days, diff.seconds
                hours = days * 24 + seconds // 3600
                sheet.update({
                    'days_no_tmp': hours if sheet.duration_type == 'hours' else days_no,
                })

    @api.onchange('overtime_type_id')
    def _get_hour_amount(self):
        if self.overtime_type_id.rule_line_ids and self.duration_type == 'hours':
            for recd in self.overtime_type_id.rule_line_ids:
                if recd.from_hrs < self.days_no_tmp <= recd.to_hrs and self.contract_id:
                    if self.contract_id.over_hour:
                        cash_amount = self.contract_id.over_hour * recd.hrs_amount
                        self.cash_hrs_amount = cash_amount
                    else:
                        raise UserError(_("Hour Overtime Needs Hour Wage in Employee Contract."))
        elif self.overtime_type_id.rule_line_ids and self.duration_type == 'days':
            for recd in self.overtime_type_id.rule_line_ids:
                if recd.from_hrs < self.days_no_tmp <= recd.to_hrs and self.contract_id:
                    if self.contract_id.over_day:
                        cash_amount = self.contract_id.over_day * recd.hrs_amount
                        self.cash_day_amount = cash_amount
                    else:
                        raise UserError(_("Day Overtime Needs Day Wage in Employee Contract."))

    def cancel(self):
        self.state = 'cancel'

    @api.onchange('date_from', 'date_to')
    def _onchange_date(self):
        current_date = datetime.now()
        if self.date_from:
            if (self.date_from > current_date):
                raise ValidationError(_("Please select a date that is not in the future."))
        if self.date_to:
            if (self.date_to > current_date):
                raise ValidationError(_("Please select a date that is not in the future."))

    def kg_request(self):
        lm_users = []

        lm_approve_users = self.env['ir.config_parameter'].sudo().get_param(
            'kg_mashirah_oil_purchase.line_manager_ids', False)

        if not lm_approve_users or lm_approve_users == '[]':
            raise ValidationError(_("Please Select Line Manager in Configuration"))

        hr_approve_users = self.env['ir.config_parameter'].sudo().get_param(
            'kg_mashirah_oil_purchase.hr_manager_ids', False)

        if not hr_approve_users or hr_approve_users == '[]':
            raise ValidationError(_("Please Select HR in Configuration"))

        finance_approve_users = self.env['ir.config_parameter'].sudo().get_param(
            'kg_mashirah_oil_purchase.finance_manager_ids', False)

        if not finance_approve_users or finance_approve_users == '[]':
            raise ValidationError(_("Please Select Finance Manager in Configuration"))

        if literal_eval(lm_approve_users):
            for i in literal_eval(lm_approve_users):
                users = self.env['res.users'].browse(i)
                if users:
                    lm_users.append(users)

            for user in lm_users:
                self.activity_schedule('kg_masirah_oil_overtime.line_manager_approval_notification',
                                       user_id=user.id,
                                       note=f' The User {self.env.user.name} request the Line Manager to approve the Overtime Request {self.name}. Please Verify and approve.')

        #
        # self.is_wait_lm = True
        self.is_lm_approved = True

    def submit_to_f(self):
        fc_approve_users = self.env['ir.config_parameter'].sudo().get_param(
            'kg_mashirah_oil_purchase.finance_manager_ids', False)

        if self.env.user.id not in literal_eval(fc_approve_users):
            raise UserError(_("You have no access to approve"))

        else:
            finance_manager_notification_activity = self.env.ref(
                'kg_masirah_oil_overtime.finance_manager_approval_notification')

            activity_1 = self.activity_ids.filtered(
                lambda l: l.activity_type_id == finance_manager_notification_activity)
            not_current_user_confirm = activity_1.filtered(lambda l: l.user_id != self.env.user)

            for ccc in not_current_user_confirm:
                ccc.unlink()

            activity_2 = self.activity_ids.filtered(
                lambda l: l.activity_type_id == finance_manager_notification_activity)
            activity_2.action_done()

            overtime_request_notification_activity = self.env.ref(
                'kg_masirah_oil_overtime.overtime_request_approval_notification')

            activity_1 = self.activity_ids.filtered(
                lambda l: l.activity_type_id == overtime_request_notification_activity)
            not_current_user_confirm = activity_1.filtered(lambda l: l.user_id != self.env.user)

            for ccc in not_current_user_confirm:
                ccc.unlink()

            activity_2 = self.activity_ids.filtered(
                lambda l: l.activity_type_id == overtime_request_notification_activity)
            activity_2.action_done()

            if self.type == 'leave' and self.overtime_type_id:
                day_hour = self.days_no_tmp / HOURS_PER_DAY
                holiday_vals = {
                    'name': 'Overtime',
                    'holiday_status_id': self.overtime_type_id.leave_type.id,
                    'number_of_days': day_hour,
                    'notes': self.desc,
                    'holiday_type': 'employee',
                    'employee_id': self.employee_id.id,
                    'state': 'confirm',
                }
                holiday = self.env['hr.leave.allocation'].sudo().create(
                    holiday_vals)
                holiday.action_validate()
                self.leave_id = holiday.id

            work_entry_type = self.env['hr.work.entry.type'].search([('code', '=', 'OVT')])
            if work_entry_type and self.employee_id.name:
                name = work_entry_type.name + ": " + self.employee_id.name
            else:
                name = ''
            work_entry_data = {
                'name': name,
                'employee_id': self.employee_id.id,
                'work_entry_type_id': work_entry_type.id,
                'date_start': self.date_from,
                'date_stop': self.date_to,
                'duration': self.days_no_tmp
            }
            work_entry = self.env['hr.work.entry'].sudo().create(work_entry_data)
            self.work_entry_id = work_entry.id

            # notification to employee :
            recipient_partners = [(4, self.current_user.partner_id.id)]
            body = "Your Time In Lieu Request Has been Approved ..."
            msg = _(body)
        return self.sudo().write({
            'state': 'approved',
        })

    def lm_approve(self):
        lm_approve_users = self.env['ir.config_parameter'].sudo().get_param(
            'kg_mashirah_oil_purchase.line_manager_ids', False)

        if self.env.user.id not in literal_eval(lm_approve_users):
            raise UserError(_("You have no access to approve"))

        else:
            line_manager_notification_activity = self.env.ref(
                'kg_masirah_oil_overtime.line_manager_approval_notification')

            activity_1 = self.activity_ids.filtered(
                lambda l: l.activity_type_id == line_manager_notification_activity)
            not_current_user_confirm = activity_1.filtered(lambda l: l.user_id != self.env.user)

            for ccc in not_current_user_confirm:
                ccc.unlink()

            activity_2 = self.activity_ids.filtered(
                lambda l: l.activity_type_id == line_manager_notification_activity)
            activity_2.action_done()

            hr_approve_users = self.env['ir.config_parameter'].sudo().get_param(
                'kg_mashirah_oil_purchase.hr_manager_ids', False)

            hr_users = []

            if literal_eval(hr_approve_users):
                for i in literal_eval(hr_approve_users):
                    users = self.env['res.users'].browse(i)
                    if users:
                        hr_users.append(users)

                for user in hr_users:
                    self.activity_schedule('kg_masirah_oil_overtime.hr_manager_approval_notification',
                                           user_id=user.id,
                                           note=f' The user {self.env.user.name} has approved the Line Manager approval and request the HR to approve the Overtime Request {self.name}. Please Verify and approve.')

            # self.is_lm_approved = True
            return self.sudo().write({
                'state': 'f_approve'
            })

    def approve(self):
        hr_approve_users = self.env['ir.config_parameter'].sudo().get_param(
            'kg_mashirah_oil_purchase.hr_manager_ids', False)
        if self.overtime_type_id and not self.overtime_type_id.leave_type:
            raise UserError(
                _('Please choose the allocated leave type from the options available under the overtime type.'))

        if self.env.user.id not in literal_eval(hr_approve_users):
            raise UserError(_("You have no access to approve"))

        else:
            hr_users = []
            hr_manager_notification_activity = self.env.ref(
                'kg_masirah_oil_overtime.hr_manager_approval_notification')

            activity_1 = self.activity_ids.filtered(
                lambda l: l.activity_type_id == hr_manager_notification_activity)
            not_current_user_confirm = activity_1.filtered(lambda l: l.user_id != self.env.user)

            for ccc in not_current_user_confirm:
                ccc.unlink()

            activity_2 = self.activity_ids.filtered(
                lambda l: l.activity_type_id == hr_manager_notification_activity)
            activity_2.action_done()

            finance_approve_users = self.env['ir.config_parameter'].sudo().get_param(
                'kg_mashirah_oil_purchase.hr_manager_ids', False)

            finance_users = []

            if literal_eval(finance_approve_users):
                for i in literal_eval(finance_approve_users):
                    users = self.env['res.users'].browse(i)
                    if users:
                        finance_users.append(users)

                for user in finance_users:
                    self.activity_schedule('kg_masirah_oil_overtime.finance_manager_approval_notification',
                                           user_id=user.id,
                                           note=f' The user {self.env.user.name} has approved the HR approval and request the Finance Manager to approve the Overtime Request {self.name}. Please Verify and approve.')


            self.is_hr_approved = True

    def reject(self):
        if not self.is_lm_approved:
            lm_approve_users = self.env['ir.config_parameter'].sudo().get_param(
                'kg_mashirah_oil_purchase.line_manager_ids', False)

            if self.env.user.id not in literal_eval(lm_approve_users):
                raise UserError(_("You have no access to reject"))

        if self.is_lm_approved:
            hr_approve_users = self.env['ir.config_parameter'].sudo().get_param(
                'kg_mashirah_oil_purchase.hr_manager_ids', False)

            if self.env.user.id not in literal_eval(hr_approve_users):
                raise UserError(_("You have no access to reject"))

        self.activity_schedule('kg_masirah_oil_overtime.reject_overtime_request_notification',
                               user_id=self.create_uid.id,
                               note=f' The user {self.env.user.name}  has rejected the approval of the Overtime Request {self.name}.')

        reject_overtime_notification_activity = self.env.ref(
            'kg_masirah_oil_overtime.reject_overtime_request_notification')
        activity = self.activity_ids.filtered(
            lambda l: l.activity_type_id == reject_overtime_notification_activity)
        activity.action_done()

        line_manager_notification_activity = self.env.ref(
            'kg_masirah_oil_overtime.line_manager_approval_notification')
        activity_1 = self.activity_ids.filtered(lambda l: l.activity_type_id == line_manager_notification_activity)
        activity_1.unlink()

        hr_manager_notification_activity = self.env.ref(
            'kg_masirah_oil_overtime.hr_manager_approval_notification')
        activity_2 = self.activity_ids.filtered(lambda l: l.activity_type_id == hr_manager_notification_activity)
        activity_2.unlink()

        finance_manager_notification_activity = self.env.ref(
            'kg_masirah_oil_overtime.finance_manager_approval_notification')
        activity_2 = self.activity_ids.filtered(lambda l: l.activity_type_id == finance_manager_notification_activity)
        activity_2.unlink()
        self.state = 'refused'

    @api.constrains('date_from', 'date_to')
    def _check_date(self):
        for req in self:
            domain = [
                ('date_from', '<=', req.date_to),
                ('date_to', '>=', req.date_from),
                ('employee_id', '=', req.employee_id.id),
                ('id', '!=', req.id),
                ('state', 'not in', ['refused']),
            ]
            nholidays = self.search_count(domain)
            if nholidays:
                raise ValidationError(_(
                    'You can not have 2 Overtime requests that overlaps on same day!'))

    @api.model
    def create(self, values):
        seq = self.env['ir.sequence'].next_by_code('hr.overtime') or '/'
        values['name'] = seq
        return super(HrOverTime, self.sudo()).create(values)

    def unlink(self):
        for overtime in self.filtered(
                lambda overtime: overtime.state != 'draft'):
            raise UserError(
                _('You cannot delete TIL request which is not in draft state.'))
        return super(HrOverTime, self).unlink()

    # @api.onchange('date_from', 'date_to', 'employee_id')
    # def _onchange_date(self):
    #     holiday = False
    #     if self.contract_id and self.date_from and self.date_to:
    #         for leaves in self.contract_id.resource_calendar_id.global_leave_ids:
    #             leave_dates = pd.date_range(leaves.date_from, leaves.date_to).date
    #             overtime_dates = pd.date_range(self.date_from, self.date_to).date
    #             for over_time in overtime_dates:
    #                 for leave_date in leave_dates:
    #                     if leave_date == over_time:
    #                         holiday = True
    #         if holiday:
    #             self.write({
    #                 'public_holiday': 'You have Public Holidays in your Overtime request.',
    #                 'over_time_day': 'public_holidays',
    #             })
    #         else:
    #             if self.date_from:
    #                 date_from_day = self.date_from.strftime('%A')
    #                 holiday = ''
    #                 if date_from_day == 'Monday':
    #                     holiday = 'week_day'
    #                 if date_from_day == 'Tuesday':
    #                     holiday = 'week_day'
    #                 if date_from_day == 'Wednesday':
    #                     holiday = 'week_day'
    #                 if date_from_day == 'Thursday':
    #                     holiday = 'week_day'
    #                 if date_from_day == 'Friday':
    #                     holiday = 'week_day'
    #                 if date_from_day == 'Saturday':
    #                     holiday = 'weekend'
    #                 if date_from_day == 'Sunday':
    #                     holiday = 'weekend'
    #             self.write({'public_holiday': ' ',
    #                         'over_time_day': holiday,
    #                         })
    #         hr_attendance = self.env['hr.attendance'].search(
    #             [('check_in', '>=', self.date_from),
    #              ('check_in', '<=', self.date_to),
    #              ('employee_id', '=', self.employee_id.id)])
    #         self.update({
    #             'attendance_ids': [(6, 0, hr_attendance.ids)]
    #         })


class HrOverTimeType(models.Model):
    _name = 'overtime.type'
    _description = "HR Overtime Type"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name')
    type = fields.Selection([('cash', 'Cash'),
                             ('leave', 'Leave ')])

    duration_type = fields.Selection([('hours', 'Hour'), ('days', 'Days')], string="Duration Type", default="hours",
                                     required=True)
    leave_type = fields.Many2one('hr.leave.type', string='Leave Type', domain="[('id', 'in', leave_compute)]")
    leave_compute = fields.Many2many('hr.leave.type', compute="_get_leave_type")
    rule_line_ids = fields.One2many('overtime.type.rule', 'type_line_id')

    @api.onchange('duration_type')
    def _get_leave_type(self):
        dur = ''
        ids = []
        if self.duration_type:
            if self.duration_type == 'days':
                dur = 'day'
            else:
                dur = 'hour'
            leave_type = self.env['hr.leave.type'].search([('request_unit', '=', dur)])
            for recd in leave_type:
                ids.append(recd.id)
            self.leave_compute = ids


class HrOverTimeTypeRule(models.Model):
    _name = 'overtime.type.rule'
    _description = "HR Overtime Type Rule"

    type_line_id = fields.Many2one('overtime.type', string='Over Time Type')
    name = fields.Char('Name', required=True)
    from_hrs = fields.Float('From', required=True)
    to_hrs = fields.Float('To', required=True)
    hrs_amount = fields.Float('Rate', required=True)
