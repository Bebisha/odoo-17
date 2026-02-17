
import logging
from collections import defaultdict
from datetime import timedelta, datetime, time, date
import calendar

from dateutil.relativedelta import relativedelta

from odoo.addons.resource.models.utils import HOURS_PER_DAY

# from addons.sale_stock.models.res_company import company
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import get_timedelta

_logger = logging.getLogger(__name__)


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    @api.depends('number_of_days_display')
    def _compute_source_doc(self):
        for leave in self:
            sick_leave_type = self.env['hr.leave.type'].search([('company_id', '=', self.env.company.id), ('name', '=', 'Sick Leave')])
            leave.is_source_doc = leave.holiday_status_id == sick_leave_type and leave.number_of_days_display > 1

    is_source_doc = fields.Boolean(compute="_compute_source_doc", store=True)
    total_leaves = fields.Float(string='Total Leaves', readonly=True, compute='_compute_total_leave')
    show_refuse_button = fields.Boolean(
        compute="_compute_show_refuse_button",
        string="Show Refuse Button",
    )
    has_approval_access = fields.Boolean(
        string="Has Approval Access",
        compute="_compute_has_approval_access",
        store=False
    )

    def action_escalation_mail(self):
        current_date = datetime.now()
        first_day_of_current_month = datetime(current_date.year, current_date.month, 1)
        """ function for escalation mail """
        for leave in self.search([('state', '=', 'confirm')]):
            if leave.create_date:
                # Check if the leave was created in the current month and year
                if leave.create_date >= first_day_of_current_month:
                    elapsed_time = current_date - leave.create_date
                    if elapsed_time >= timedelta(hours=48):
                        leave.action_approve()

    def _compute_has_approval_access(self):
        """Compute if the user has approval access."""
        has_access = self.env.user.has_group('kg_attendance.all_approval_access')
        for record in self:
            record.has_approval_access = has_access

    @api.depends('date_from')
    def _compute_show_refuse_button(self):
        for leave in self:
            leave.show_refuse_button = (
                    leave.date_from and leave.date_from.date() < date.today()
            )

    @api.depends('employee_id', 'employee_ids')
    def _compute_total_leave(self):
        """ compute function to calculate the leave balance """
        for rec in self:
            current_year = datetime.now().year
            start_of_year = datetime(current_year, 1, 1)
            end_of_year = datetime(current_year, 12, 31)
            hr_leave_allocation_id = self.env['hr.leave.allocation'].search([
                ('employee_id', '=', rec.employee_id.id),
                ('holiday_status_id', '=', rec.holiday_status_id.id),
                ('state', '=', 'validate'),
                ('date_from', '>=', start_of_year),
                ('date_to', '<=', end_of_year),
            ])

            hr_leave_id = self.env['hr.leave'].search(
                [('employee_id', '=', rec.employee_id.id), ('holiday_status_id', '=', rec.holiday_status_id.id),
                 ('state', 'in', ['validate', 'validate1']), ('request_date_from', '>=', start_of_year),
                 ('request_date_to', '<=', end_of_year)])
            if hr_leave_allocation_id:
                if hr_leave_id:
                    leave_total = sum(hr_leave_allocation_id.mapped('number_of_days'))
                    balance_leave = leave_total - sum(hr_leave_id.mapped('number_of_days'))
                    rec.total_leaves = balance_leave
                else:
                    rec.total_leaves = sum(hr_leave_allocation_id.mapped('number_of_days'))
            else:
                rec.total_leaves = 0.0

    def action_approve(self):
        res = super(HrLeave, self).action_approve()
        if self.env.user.has_group('kg_attendance.all_approval_access'):
            self.action_validate()
        return res

    @api.model
    def create(self, vals):
        employee = self.env['hr.employee'].browse(vals.get('employee_id'))
        # allocation_type = vals.get('allocation_type')
        if employee.company_id.country_code == 'AE':
            if employee.date_joining:
                one_year_date = employee.date_joining + timedelta(days=182)
                allocation = self.env['hr.leave.allocation'].search([
                    ('employee_id', '=', employee.id),
                    ('holiday_status_id', '=', vals.get('holiday_status_id')),
                    ('state', '=', 'validate'),
                    ('accrual_plan_id', '!=', False),

                ])

                leave_type = self.env['hr.leave.type'].browse(vals.get('holiday_status_id'))
                # Commented for approval process of employee less than 6 months
                # if allocation:
                #     if leave_type.time_off_type == 'is_annual' and fields.Date.today() < one_year_date:
                #         raise ValidationError(
                #             _("To be eligible to request annual leave, you must have completed 6 months of service "
                #               )
                #         )
                # else:
                #     raise ValidationError(
                #         _("Employee doesn't have existing allocations for this leave type.")
                #     )

        if employee.company_id.country_code == 'IN':
            if employee.date_joining:
                three_months_date = employee.date_joining + timedelta(days=90)
                leave_type = self.env['hr.leave.type'].browse(vals.get('holiday_status_id'))
                if (leave_type.time_off_type != 'is_unpaid'
                        and fields.Date.today() < three_months_date):
                    raise ValidationError(
                        _("The employee has not yet completed three months from their joining date, so leave requests cannot be processed."))
        return super(HrLeave, self).create(vals)

    def activity_update(self):
        to_clean, to_do, to_do_confirm_activity = self.env['hr.leave'], self.env['hr.leave'], self.env['hr.leave']
        activity_vals = []
        today = fields.Date.today()
        model_id = self.env.ref('hr_holidays.model_hr_leave').id
        confirm_activity = self.env.ref('hr_holidays.mail_act_leave_approval')
        approval_activity = self.env.ref('hr_holidays.mail_act_leave_second_approval')
        for holiday in self:
            if holiday.state == 'draft':
                to_clean |= holiday
            elif holiday.state in ['confirm', 'validate1']:
                if holiday.holiday_status_id.leave_validation_type != 'no_validation':
                    if holiday.state == 'confirm':
                        activity_type = confirm_activity
                        note = _(
                            'New %(leave_type)s Request created by %(user)s',
                            leave_type=holiday.holiday_status_id.name,
                            user=holiday.create_uid.name,
                        )
                    else:
                        activity_type = approval_activity
                        note = _(
                            'Second approval request for %(leave_type)s',
                            leave_type=holiday.holiday_status_id.name,
                        )
                        to_do_confirm_activity |= holiday
                    user_ids = holiday.sudo()._get_responsible_for_approval().ids or self.env.user.ids
                    for user_id in user_ids:
                        date_deadline = (
                            (holiday.date_from -
                             relativedelta(**{activity_type.delay_unit: activity_type.delay_count or 0})).date()
                            if holiday.date_from else today)
                        if date_deadline < today:
                            date_deadline = today
                        activity_vals.append({
                            'activity_type_id': activity_type.id,
                            'automated': True,
                            'date_deadline': date_deadline,
                            'note': note,
                            'user_id': user_id,
                            'res_id': holiday.id,
                            'res_model_id': model_id,
                            'summary': holiday.name
                        })
            elif holiday.state == 'validate':
                to_do |= holiday
            elif holiday.state == 'refuse':
                to_clean |= holiday
        if to_clean:
            to_clean.activity_unlink(
                ['hr_holidays.mail_act_leave_approval', 'hr_holidays.mail_act_leave_second_approval'])
        if to_do_confirm_activity:
            to_do_confirm_activity.activity_feedback(['hr_holidays.mail_act_leave_approval'])
        if to_do:
            to_do.activity_feedback(
                ['hr_holidays.mail_act_leave_approval', 'hr_holidays.mail_act_leave_second_approval'])
        self.env['mail.activity'].with_context(short_name=False).create(activity_vals)

    def _notify_get_recipients_groups(self, message, model_description, msg_vals=None):
        """ Handle HR users and officers recipients that can validate or refuse holidays
        directly from email. """
        groups = super()._notify_get_recipients_groups(
            message, model_description, msg_vals=msg_vals
        )
        if not self:
            return groups

        local_msg_vals = dict(msg_vals or {})

        self.ensure_one()
        hr_actions = []
        if self.state == 'confirm':
            app_action = self._notify_get_action_link('controller', controller='/leave/validate', **local_msg_vals)
            hr_actions += [{'url': app_action, 'title': _('Approve')}]
        if self.state in ['confirm', 'validate', 'validate1'] and not self.show_refuse_button:
            ref_action = self._notify_get_action_link('controller', controller='/leave/refuse', **local_msg_vals)
            hr_actions += [{'url': ref_action, 'title': _('Reject')}]

        holiday_user_group_id = self.env.ref('hr_holidays.group_hr_holidays_user').id
        new_group = (
            'group_hr_holidays_user',
            lambda pdata: pdata['type'] == 'user' and holiday_user_group_id in pdata['groups'],
            {
                'actions': hr_actions,
                'active': True,
                'has_button_access': True,
            }
        )

        return [new_group] + groups


class HrLeaveAllocation(models.Model):
    _inherit = 'hr.leave.allocation'

    manual_override = fields.Boolean('Manual Override', default=False)
    number_of_days_display = fields.Float(
        'Duration (days)', compute='_compute_number_of_days_display', store=True,
        help="For an Accrual Allocation, this field contains the theoretical amount of time given to the employee."
    )

    @api.depends('number_of_days', 'manual_override')
    def _compute_number_of_days_display(self):
        for allocation in self:
            # If manual override is True, use the manual value
            if allocation.manual_override:
                continue  # Do nothing, keep the manually set value
            # Otherwise, compute it based on number_of_days
            allocation.number_of_days_display = allocation.number_of_days

    def _selection_holiday_type(self):
        options = [
            ('employee', 'By Employee'),
            ('company', 'By Company'),
            ('department', 'By Department')
        ]
        return options

    holiday_type = fields.Selection(selection='_selection_holiday_type',
                                    string='Allocation Mode', readonly=False,
                                    required=True, default='employee',
                                    help="Allow to create requests in batch:\n"
                                         "- By Employee: for a specific employee\n"
                                         "- By Company: all employees of the specified company\n"
                                         "- By Department: all employees of the specified department")

    company_name = fields.Many2one('res.company', default=lambda self: self.env.company, string="Company")

    @api.model
    def automate_accrual_leave_allocation(self):
        print('Accrual allocation started')

        employees = self.env['hr.employee'].search(
            [('active', '=', True), ('company_id.country_code', 'in', ['AE', 'BH', 'OM'])])

        current_date = fields.Date.today()
        current_year_start = date(current_date.year, 1, 1)  # Start of the current year
        previous_year_start = datetime(current_date.year - 1, 1, 1).date()
        previous_year_end = datetime(current_date.year - 1, 12, 31).date()

        for employee in employees:
            joining_date = employee.date_joining
            if not joining_date:
                continue

            effective_joining_date = max(joining_date, current_year_start)

            months_worked = relativedelta(current_date, joining_date).months + (
                    relativedelta(current_date, joining_date).years * 12)
            if months_worked < 6:
                print(f"{employee.name} has not completed 6 months yet. Skipping allocation.")
                continue

            months_since_joining = relativedelta(current_date, effective_joining_date).months
            if months_since_joining <= 0:
                continue

            company_id = employee.company_id
            print("company_idsssssssssssss",company_id)
            accrual_plan = self.env['hr.leave.accrual.plan'].sudo().search([('company_id', 'in', [False, company_id.id])],
                                                                    limit=1)
            print(accrual_plan, "Accrual Plan")

            if not accrual_plan:
                continue

            rule = accrual_plan.level_ids.filtered(lambda x: x.accrual_plan_id == accrual_plan)
            applicable_level = rule.added_value
            print(applicable_level, "Applicable Level")

            accrued_days = months_since_joining * applicable_level
            print(f"{employee.name} has accrued {accrued_days} days based on {months_since_joining} months worked")

            # Check for carry-forward from the previous year
            previous_allocations = self.env['hr.leave.allocation'].search([
                ('employee_id', '=', employee.id),
                ('holiday_status_id', '=', self.env['hr.leave.type'].search(
                    [('company_id', '=', self.env.company.id), ('name', '=', 'Paid Leave')]).id),
                ('date_from', '>=', previous_year_start),
                ('date_to', '<=', previous_year_end),
                ('state', '=', 'validate')  # Only validated allocations
            ])
            print('previous_allocations')

            total_allocated_days = sum(allocation.number_of_days for allocation in previous_allocations)
            print(f"Total allocated days for {employee.name} in the previous year: {total_allocated_days}")

            # Get all leaves taken by the employee in the previous year
            leaves_taken_last_year = self.env['hr.leave'].search([
                ('employee_id', '=', employee.id),
                ('holiday_status_id', '=', self.env['hr.leave.type'].search(
                    [('company_id', '=', self.env.company.id), ('name', '=', 'Paid Leave')]).id),
                ('request_date_from', '>=', previous_year_start),
                ('request_date_to', '<=', previous_year_end),
                ('state', '=', 'validate')
            ])

            total_leaves_taken = sum(leave.number_of_days_display for leave in leaves_taken_last_year)
            print(f"Total leaves taken by {employee.name} in the previous year: {total_leaves_taken}")

            # Calculate exact pending leaves
            pending_leaves = total_allocated_days - total_leaves_taken
            print(f"Pending leaves for {employee.name}: {pending_leaves}")
            pend_lev = 15

            # Fix: Carry forward leaves as long as they are greater than 0, but max 4 days
            if pending_leaves > 0:
                carry_forward_days = min(pending_leaves, pend_lev)  # Carry forward up to 4 days max
                print(f"Carrying forward {carry_forward_days} days for {employee.name}")
                holiday_status = self.env['hr.leave.type'].search([('time_off_type', '=', 'is_carry')],
                                                                  limit=1).id
                # Create carry-forward leave allocation
                if carry_forward_days > 0 and holiday_status:
                    validity_stop = datetime(current_date.year, 3, 31).date()
                    cl_carry = self.env['hr.leave.allocation'].create({
                        'employee_id': employee.id,
                        'holiday_status_id': holiday_status if holiday_status else False,
                        'number_of_days': carry_forward_days,
                        'manual_override': True,
                        'number_of_days_display': carry_forward_days,
                        'allocation_type': 'accrual',
                        'name': f"Carry Forward Paid Leave for {current_date.year}",
                        'date_from': current_year_start,
                        'date_to': validity_stop,
                    })
                    cl_carry.action_validate()
                    print(cl_carry.holiday_status_id, "hrthrthrt")
                    print(f"{carry_forward_days} carry-forward leave days allocated to {employee.name}")
            else:
                print(f"No carry forward for {employee.name}")

            # Check for existing allocations in the current year
            existing_allocation = self.env['hr.leave.allocation'].search([
                ('employee_id', '=', employee.id),
                ('accrual_plan_id', '=', accrual_plan.id),
                ('holiday_status_id', '=', self.env['hr.leave.type'].search(
                    [('company_id', '=', self.env.company.id), ('name', '=', 'Paid Leave')]).id),
                ('date_from', '>=', current_year_start)
            ], limit=1)

            if existing_allocation:
                print(f"Allocation already exists for {employee.name}. Skipping creation.")
                continue

            # Create new accrued leave allocation
            if accrued_days > 0 and employee.company_id.country_code in ['AE', 'BH', 'OM']:
                allocation = self.env['hr.leave.allocation'].create({
                    'employee_id': employee.id,
                    'holiday_status_id': self.env['hr.leave.type'].search(
                        [('company_id', '=', self.env.company.id), ('name', '=', 'Paid Leave')]).id,
                    'number_of_days': accrued_days,
                    'accrual_plan_id': accrual_plan.id,
                    'allocation_type': 'accrual',
                    'name': f"Accrual Timeoff Allocation for {employee.name}",
                    'date_from': effective_joining_date,
                })
                print(allocation.employee_id, "Allocation Created")
                allocation.action_validate()
                print(f"Accrued time off allocated to {employee.name}: {accrued_days} days")

    @api.model
    def cron_update_days(self):
        allocations = self.env['hr.leave.allocation'].search(
            [('allocation_type', '=', 'accrual'),
             ('holiday_status_id.time_off_type', '=', 'is_annual'), ('state', '=', 'validate')])

        for rec in allocations:
            today = fields.Date.today()
            start_date = rec.date_from
            if not start_date:
                continue

            end_date = rec.date_to or today

            if today <= end_date:
                months_elapsed = (today.year - start_date.year) * 12 + (
                        today.month - start_date.month)

                accrual_per_month = rec.accrual_plan_id.level_ids[0].added_value
                max_allocated_leaves = rec.accrual_plan_id.level_ids[0].maximum_leave

                accrued_leaves = months_elapsed * accrual_per_month
                accrued = min(accrued_leaves, max_allocated_leaves)

                rec.number_of_days = accrued

    # @api.model
    # def cron_automate_accrual_timeoff_allocation(self):
    #     print('cron_automate_accrual_timeoff_allocation', self.env.company.country_code)
    #     if self.env.company.country_code in ['AE', 'BH', 'OM']:
    #         self.automate_accrual_leave_allocation()

    # Automatic Leave Allocation

    # @api.model
    # def automate_annual_leave_allocation(self):
    #     print('Regular allocation')
    #     # Get employees from Indian companies only
    #     employees = self.env['hr.employee'].search([
    #         ('active', '=', True),
    #         ('company_id.country_code', '=', 'IN')
    #     ])
    #     current_date = fields.Date.today()
    #     current_year = current_date.year
    #
    #     for employee in employees:
    #         print("Employee", employee)
    #         joining_date = employee.date_joining
    #         if joining_date:
    #             year_start = datetime(current_year, 1, 1).date()
    #             year_end = datetime(current_year, 12, 31).date()
    #
    #             # Check if leave allocation already exists for the current year
    #             existing_allocations = self.env['hr.leave.allocation'].search([
    #                 ('employee_id', '=', employee.id),
    #                 ('holiday_status_id', 'in', [
    #                     self.env['hr.leave.type'].search(
    #                         [('company_id', '=', self.env.company.id), ('name', '=', 'Casual Leave')]).id,
    #                     self.env['hr.leave.type'].search(
    #                         [('company_id', '=', self.env.company.id), ('name', '=', 'Sick Leave')]).id
    #                 ]),
    #                 ('date_from', '>=', year_start),
    #                 ('date_to', '<=', year_end),
    #             ])
    #             print(existing_allocations, 'existing_allocations')
    #
    #             if existing_allocations:
    #                 continue
    #             print('existing_allocations2')
    #
    #             # Get the previous year's allocation
    #             previous_year_start = datetime(current_year - 1, 1, 1).date()
    #             previous_year_end = datetime(current_year - 1, 12, 31).date()
    #
    #             # Sum all allocations from the previous year for the employee
    #             previous_allocations = self.env['hr.leave.allocation'].search([
    #                 ('employee_id', '=', employee.id),
    #                 ('holiday_status_id', '=', self.env['hr.leave.type'].search(
    #                     [('company_id', '=', self.env.company.id), ('name', '=', 'Casual Leave')]).id),
    #                 ('date_from', '>=', previous_year_start),
    #                 ('date_to', '<=', previous_year_end),
    #                 ('state', '=', 'validate')  # Only validated allocations
    #             ])
    #             print('previous_allocations')
    #
    #             total_allocated_days = sum(allocation.number_of_days for allocation in previous_allocations)
    #             print(f"Total allocated days for {employee.name} in the previous year: {total_allocated_days}")
    #
    #             # Get all leaves taken by the employee in the previous year
    #             leaves_taken_last_year = self.env['hr.leave'].search([
    #                 ('employee_id', '=', employee.id),
    #                 ('holiday_status_id', '=', self.env['hr.leave.type'].search(
    #                     [('company_id', '=', self.env.company.id), ('name', '=', 'Casual Leave')]).id),
    #                 ('request_date_from', '>=', previous_year_start),
    #                 ('request_date_to', '<=', previous_year_end),
    #                 ('state', '=', 'validate')  # Only validated leaves
    #             ])
    #
    #             total_leaves_taken = sum(leave.number_of_days_display for leave in leaves_taken_last_year)
    #             print(f"Total leaves taken by {employee.name} in the previous year: {total_leaves_taken}")
    #
    #             # Calculate exact pending leaves
    #             pending_leaves = total_allocated_days - total_leaves_taken
    #             print(f"Pending leaves for {employee.name}: {pending_leaves}")
    #             pend_lev = 4
    #
    #             # Fix: Carry forward leaves as long as they are greater than 0, but max 4 days
    #             if pending_leaves > 0:
    #                 carry_forward_days = min(pending_leaves, pend_lev)  # Carry forward up to 4 days max
    #                 print(f"Carrying forward {carry_forward_days} days for {employee.name}")
    #                 holiday_status = self.env['hr.leave.type'].search([('time_off_type', '=', 'is_carry')],
    #                                                                   limit=1).id
    #                 if carry_forward_days > 0 and employee.company_id.country_code == 'IN' and holiday_status:
    #                     validity_stop = datetime(current_year, 3, 31).date()
    #                     print(validity_stop,"eeeeeeeeeeeeeeefrf")
    #                     # Create Carry Forward allocation
    #                     cl_carry = self.env['hr.leave.allocation'].create({
    #                         'employee_id': employee.id,
    #                         'holiday_status_id':  holiday_status if holiday_status else False,
    #                         'number_of_days': carry_forward_days,
    #                         'manual_override': True,
    #                         'number_of_days_display': carry_forward_days,
    #                         'allocation_type': 'regular',
    #                         'name': f"Carry Forward Casual Leave for {current_year}",
    #                         'date_from': year_start,
    #                         'date_to': validity_stop,
    #                     })
    #                     cl_carry.action_validate()
    #                     print(f"{carry_forward_days} carry-forward leave days allocated to {employee.name}")
    #             else:
    #                 print(f"No carry forward for {employee.name}")
    #
    #             # Full allocation if joined before the year start, else prorated
    #             if joining_date <= year_start:
    #                 casual_leave_days = 8  # Full allocation with carry forward
    #                 sick_leave_days = 4
    #             else:
    #                 three_months_after_joining = joining_date + timedelta(days=90)
    #                 if current_date < three_months_after_joining:
    #                     continue
    #
    #                 remaining_days = (year_end - three_months_after_joining).days + 1
    #                 casual_leave_days = round((remaining_days / 365) * 8.00)
    #                 sick_leave_days = round((remaining_days / 365) * 4.00)
    #             print('casual_leave_days', casual_leave_days)
    #             print('sick_leave_days', sick_leave_days)
    #
    #             # Casual Leave Allocation for the current year
    #             if casual_leave_days > 0 and employee.company_id.country_code == 'IN':
    #                 cl_allocation = self.env['hr.leave.allocation'].create({
    #                     'employee_id': employee.id,
    #                     'holiday_status_id': self.env['hr.leave.type'].search(
    #                         [('company_id', '=', self.env.company.id), ('name', '=', 'Casual Leave')]).id,
    #                     'number_of_days': casual_leave_days,
    #                     'manual_override': True,
    #                     'number_of_days_display': casual_leave_days,
    #                     'allocation_type': 'regular',
    #                     'name': f"Casual Leave Allocation for {current_year}",
    #                     'date_from': year_start,
    #                     'date_to': year_end,
    #                 })
    #                 cl_allocation.action_validate()
    #
    #             # Sick Leave Allocation
    #             if sick_leave_days > 0 and employee.company_id.country_code == 'IN':
    #                 sil_allocation = self.env['hr.leave.allocation'].create({
    #                     'employee_id': employee.id,
    #                     'holiday_status_id': self.env['hr.leave.type'].search(
    #                         [('company_id', '=', self.env.company.id), ('name', '=', 'Sick Leave')]).id,
    #                     'number_of_days': sick_leave_days,
    #                     'manual_override': True,
    #                     'number_of_days_display': sick_leave_days,
    #                     'allocation_type': 'regular',
    #                     'name': f"Sick Leave Allocation for {current_year}",
    #                     'date_from': year_start,
    #                     'date_to': year_end,
    #                 })
    #                 sil_allocation.action_validate()

    # @api.model
    # def cron_automate_annual_allocation(self):
    #     print('cron_automate_annual_allocation', self.env.company.country_code)
    #     if self.env.company.country_code == 'IN':
    #         self.automate_annual_leave_allocation()

    # Sick Leave Allocation

    # @api.model
    # def ir_automate_sick_leave_allocation(self):
    #     print('Sick leave allocation started')
    #     employees = self.env['hr.employee'].search([
    #         ('active', '=', True),
    #         ('company_id.country_code', 'in', ['AE', 'BH','OM'])
    #     ])
    #     current_date = fields.Date.today()
    #     current_year = current_date.year
    #
    #     for employee in employees:
    #         # Ensure company is based in Dubai (AE)
    #         dubai_company = employee.company_id.country_code in ['AE', 'BH','OM']
    #         if not dubai_company:
    #             print(f"Skipping {employee.name} as their company is not in Dubai (AE).")
    #             continue
    #
    #         joining_date = employee.date_joining
    #         if joining_date:
    #             year_start = datetime(current_year, 1, 1).date()
    #             year_end = datetime(current_year, 12, 31).date()
    #
    #             is_leap_year = calendar.isleap(current_year)
    #             total_days_in_year = 366 if is_leap_year else 365
    #
    #             # Check if allocation already exists for the current year
    #             existing_allocations = self.env['hr.leave.allocation'].search([
    #                 ('employee_id', '=', employee.id),
    #                 ('holiday_status_id', 'in', [
    #                     self.env['hr.leave.type'].search(
    #                         [('company_id', '=', self.env.company.id), ('name', '=', 'Paid Leave')]).id,
    #                     self.env['hr.leave.type'].search(
    #                         [('company_id', '=', self.env.company.id), ('name', '=', 'Sick Leave')]).id
    #                 ]),
    #                 ('date_from', '>=', year_start),
    #                 ('date_to', '<=', year_end),
    #                 ('state', '=', 'validate')  # Ensure only validated allocations are considered
    #             ])
    #
    #             if existing_allocations:
    #                 print(f"Leave allocation already exists for {employee.name} in {current_year}. Skipping...")
    #                 continue
    #
    #             # Previous year's casual leave allocation
    #             previous_year_start = datetime(current_year - 1, 1, 1).date()
    #             previous_year_end = datetime(current_year - 1, 12, 31).date()
    #
    #             previous_cl_allocation = self.env['hr.leave.allocation'].search([
    #                 ('employee_id', '=', employee.id),
    #                 ('holiday_status_id', '=', self.env['hr.leave.type'].search(
    #                     [('company_id', '=', self.env.company.id), ('name', '=', 'Paid Leave')]).id),
    #                 ('date_from', '>=', previous_year_start),
    #                 ('date_to', '<=', previous_year_end),
    #                 ('state', '=', 'validate')
    #             ], limit=1)
    #
    #             if previous_cl_allocation:
    #                 remaining_leaves = previous_cl_allocation.number_of_days - previous_cl_allocation.leaves_taken
    #                 print(f"Remaining leaves from last year for {employee.name}: {remaining_leaves}")
    #
    #             # Sick leave calculation logic
    #             if joining_date <= year_start:
    #                 sick_leave_days = 14  # Full year allowance
    #             else:
    #                 # Calculate sick leave after 3 months of joining
    #                 three_months_after_joining = joining_date + timedelta(days=90)
    #                 if three_months_after_joining > year_end:
    #                     continue  # If the 3-month period exceeds the year end, skip
    #                 remaining_days = (year_end - three_months_after_joining).days + 1
    #                 sick_leave_days = round((remaining_days / total_days_in_year) * 14)
    #
    #             # Create sick leave allocation if applicable
    #             if sick_leave_days > 0 and employee.company_id.country_code in ['AE', 'BH', 'OM']:
    #                 sl_allocation = self.env['hr.leave.allocation'].create({
    #                     'employee_id': employee.id,
    #                     'holiday_status_id': self.env['hr.leave.type'].search(
    #                         [('company_id', '=', self.env.company.id), ('name', '=', 'Sick Leave')]).id,
    #                     'number_of_days': sick_leave_days,
    #                     'manual_override': True,
    #                     'number_of_days_display': sick_leave_days,
    #                     'allocation_type': 'regular',
    #                     'name': f"Sick Leave Allocation for {current_year}",
    #                     'date_from': year_start,
    #                     'date_to': year_end,
    #                 })
    #                 sl_allocation.action_validate()
    #                 print(f"Sick Leave allocation created for {employee.name}: {sick_leave_days} days.")

    # @api.model
    # def ir_cron_automate_sick_allocation(self):
    #     print('ir_cron_automate_sick_allocation', self.env.company.country_code)
    #     if self.env.company.country_code in ['AE', 'BH', 'OM']:
    #         self.ir_automate_sick_leave_allocation()

class HrEmployee(models.Model):
    _inherit = 'hr.leave.type'

    time_off_type = fields.Selection([('is_sick','Sick'),('is_casual','Casual'),('is_unpaid','Unpaid'),('is_annual','Annual'),('is_carry', 'Carry Forward')])

    # is_carry_forward = fields.Boolean(string="Is Carry Forward")
    time_off_type = fields.Selection(
        [('is_sick', 'Sick'), ('is_casual', 'Casual'), ('is_unpaid', 'Unpaid'),('is_carry', 'Carry Forward'),
         ('is_annual', 'Annual')])
