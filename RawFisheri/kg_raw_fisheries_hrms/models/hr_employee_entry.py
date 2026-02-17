# -*- coding: utf-8 -*-
from datetime import datetime, timedelta, date

from reportlab.graphics.transform import inverse

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class HREmployeeEntry(models.Model):
    _name = 'hr.employee.entry'
    _description = 'hr.employee.entry'

    name = fields.Char(string="Description")
    employee_id = fields.Many2one(
        'hr.employee',
        string="Employee",
        domain=lambda self: self._get_employee_domain(),
        required=True
    )
    vessel_id = fields.Many2one('sponsor.sponsor', string="Vessel", related="employee_id.sponsor_name")
    vessels_id = fields.Many2one('sponsor.sponsor', string="Vessel")
    parent_id = fields.Many2one('hr.employee', string="Manager", related="employee_id.parent_id", store=True)
    factory_manager_ids = fields.Many2many(related='employee_id.factory_manager_ids', string="Factory Manager")
    over_time = fields.Float(string="OT")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    duration = fields.Float(string="Duration", compute='_compute_duration')
    absent_days = fields.Float(string="Absent Days")
    bonus = fields.Float(string="Extra Income")
    holiday_allowance = fields.Float(string="Holiday Allowance")
    discharge_qty = fields.Float(string="Discharge Amount", compute='_compute_discharge_amount',
                                 inverse='_inverse_discharge_amount')
    # discharge_qty = fields.Float(string="Discharge Amount", compute='_compute_discharge_amount')
    total_allowance = fields.Float(string="Total", compute='_compute_total_allowance')
    state = fields.Selection([('draft', "Draft"), ('to_approve', "To Approve"), ('approved', "Approved")],
                             string="State", default='draft')
    shop_deduction = fields.Float(string="Shop Deduction", compute='_compute_shop_deduction',
                                  inverse='_inverse_shop_deduction')
    # shop_deduction = fields.Float(string="Shop Deduction", compute='_compute_shop_deduction')
    penalty = fields.Float(string="Penalty")
    travelling_days = fields.Integer(string="Travelling Days")
    user_has_group_factory_manager = fields.Boolean(compute='_compute_is_fm')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    salary_pre_payment = fields.Float(string='Salary Advance', compute='_compute_advance_salary')

    @api.model
    def _get_employee_domain(self):
        """ Domain set for field employee_id """
        hr_manager_group = self.env.ref('kg_raw_fisheries_hrms.hr_manager', raise_if_not_found=False)
        if hr_manager_group and hr_manager_group.id in self.env.user.groups_id.ids:
            return [('parent_id.user_id', '=', self.env.user.id)]
        else:
            return [('factory_manager_ids.user_id', '=', self.env.user.id)]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            employee = self.env['hr.employee'].browse(vals.get('employee_id'))
            if not employee.exists():
                raise UserError("Employee record not found!")
            if not employee.contract_id:
                raise UserError(f"You cannot create an entry for {employee.name} without a contract!")
            # if employee.contract_id.date_end and employee.contract_id.date_end <= vals.get(
            #         'end_date') and employee.contract_id.state == 'close':
            #     raise UserError(f"You cannot create an entry for {employee.name} who is already signed off!")
        return super().create(vals_list)

    def submit_for_approval(self):
        """ Process of submitting entries for approval """
        for entry in self:
            if entry.state == 'draft':
                entry.write({'state': 'to_approve'})

    def action_approve(self):
        """ Approval Process for Employee Entries """
        for entry in self:
            # if entry.state == 'to_approve':
            entry.write({'state': 'approved'})

    def action_set_to_draft(self):
        """ Function to add edit option after approval """
        for entry in self:
            if entry.state == 'approved':
                entry.write({'state': 'draft'})

    @api.depends('start_date', 'end_date', 'absent_days',
                 'travelling_days')
    def _compute_duration(self):
        """ To calculate duration on the basis of start date and end date """
        for entry in self:
            if entry.end_date and entry.start_date:
                days = (entry.end_date - entry.start_date).days + 1
            else:
                days = 0
            entry.duration = days - entry.absent_days + entry.travelling_days

    @api.onchange('start_date', 'end_date')
    def _onchange_dates(self):
        """ To make sure that the entries are made in the contract period itself """
        for entry in self:
            if entry.employee_id.contract_id:
                if entry.start_date and entry.start_date < entry.employee_id.contract_id.date_start:
                    raise ValidationError("The Entry Start Date cannot be before Employee Sign on!")
                if entry.end_date and entry.employee_id.contract_id.date_end and entry.end_date > entry.employee_id.contract_id.date_end:
                    raise ValidationError("The Entry End Date cannot be after Employee Sign off!")
            entries = self.env['hr.employee.entry'].search([])
            entries = self.env['hr.employee.entry'].search(
                [('employee_id', '=', entry.employee_id.id), ('id', '!=', entry._origin.id),
                 ('start_date', '>=', entry.start_date), ('end_date', '<=', entry.end_date)])

    @api.depends('employee_id', 'start_date', 'end_date')
    def _compute_is_fm(self):
        """ To compute whether the current ser is a factory manager """
        current_user = self.env.user
        user_has_group_factory_manager = current_user.has_group('kg_raw_fisheries_hrms.factory_manager')
        for entry in self:
            entry.user_has_group_factory_manager = user_has_group_factory_manager

    @api.depends('employee_id', 'start_date', 'end_date', 'vessels_id')
    def _compute_shop_deduction(self):
        """ To compute the shop deduction from shop entry """
        for entry in self:
            shop_deduction = sum(self.env['shop.entry'].search(
                [('employee_id', '=', entry.employee_id.id), ('state', '=', 'approved'),
                 ('vessel_id', '=', entry.vessels_id.id),
                 ('date', '>=', entry.start_date), ('date', '<=', entry.end_date)]).mapped('amount'))
            entry.write({
                'shop_deduction': shop_deduction,
            })

    def _inverse_shop_deduction(self):
        """ Handle manual updates to the shop deduction """
        pass

    @api.depends('employee_id', 'start_date', 'end_date', 'vessels_id')
    def _compute_discharge_amount(self):
        """Compute the total discharge amount from approved discharge entries."""
        for entry in self:
            end_date = entry.end_date or date.today()

            discharges = self.env['hr.discharge'].search([
                ('employee_id', '=', entry.employee_id.id),
                ('state', '=', 'approved'),
                ('vessel_id', '=', entry.vessels_id.id),
                ('amount', '>', 0),
                ('start_date', '<=', end_date),
                '|',
                ('date', '>=', entry.start_date),
                ('date', '=', False)
            ])

            total_amount = sum(d.amount for d in discharges)
            entry.discharge_qty = total_amount

    def _inverse_discharge_amount(self):
        """ Handle manual updates to the discharge amount """
        pass

    @api.depends('employee_id', 'start_date', 'end_date')
    def _compute_advance_salary(self):
        """ To compute the salary advance amount from salary prepayments """
        for entry in self:
            salary_pre_payment = sum(self.env['salary.pre.payment'].search(
                [('employee_id', '=', entry.employee_id.id), ('state', '=', 'approved'),
                 ('paid_date', '>', entry.start_date), ('paid_date', '<', entry.end_date)]).mapped('amount'))
            entry.write({
                'salary_pre_payment': salary_pre_payment,
            })

    @api.depends('employee_id', 'bonus', 'discharge_qty')
    def _compute_total_allowance(self):
        """ To compute the total allowance of the employee """
        for entry in self:
            entry.write({
                'total_allowance': entry.bonus + entry.discharge_qty + entry.over_time,
            })

    @api.model
    def _create_employee_entries(self):
        """ To update the Employee Entries """
        today = fields.Date.today()

        if today.day == 1:
            entries = self.env['hr.employee.entry'].search([('start_date', '=', today)])
            employees = self.env['hr.employee'].search([('crew', '=', True), ('contract_id', '!=', False)])
            if not entries:
                for employee in employees:
                    vals = {
                        'employee_id': employee.id,
                        'vessels_id': employee.sponsor_name.id,
                        'start_date': today,
                    }
                    self.env['hr.employee.entry'].create(vals)
