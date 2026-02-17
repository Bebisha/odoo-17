# -*- coding: utf-8 -*-


from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class HREmployeeEntry(models.Model):
    _name = 'hr.employee.entry'
    _description = 'hr.employee.entry'

    name = fields.Char(string="Description")
    employee_id = fields.Many2one(
        'hr.employee',
        string="Employee",

        required=True
    )
    vessel_id = fields.Char("Vessel")
    vessel_code_id = fields.Many2one('vessel.code', string='Vessel')
    parent_id = fields.Many2one('hr.employee', string="Manager", store=True)

    over_time = fields.Float(string="OT", compute='_compute_overtime_deduction')
    over_time_rate = fields.Float(string="OT Rate")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    # duration = fields.Float(string="Duration", compute='_compute_duration')
    duration = fields.Float(string="Duration")
    absent_days = fields.Float(string="Absent Days")
    bonus = fields.Float(string="Extra Income")
    holiday_allowance = fields.Float(string="Holiday Allowance")
    type_entry = fields.Selection(
        [('overseas_entries', "Overseas"), ('anchorage_entry', "Anchorage"), ('overtime', "Timesheet Overtime"),
         ('overtime_fixed_allowance', "Attendance Overtime")],
        string="Type of Entry", default='overseas_entries')

    total_allowance = fields.Float(string="Total")
    state = fields.Selection([('draft', "Draft"), ('to_approve', "To Approve"), ('approved', "Approved")],
                             string="State", default='draft')
    overseas_deduction = fields.Float(string="Overseas", compute='_compute_overseas_deduction', readonly=True)
    anchorage_deduction = fields.Float(string="Anchorage", compute='_compute_anchorage_deduction', readonly=True)
    penalty = fields.Float(string="Penalty")
    travelling_days = fields.Integer(string="Travelling Days")
    user_has_group_factory_manager = fields.Boolean(compute='_compute_is_fm')
    currency_id = fields.Many2one('res.currency', string='Currency')

    @api.depends('employee_id', 'duration', 'type_entry')
    def _compute_overtime_deduction(self):
        """Compute the total overtime or fixed allowance based on employee contract details."""
        for entry in self:
            entry.over_time = 0.00
            if entry.employee_id and entry.employee_id.contract_id and entry.type_entry in ['overtime',
                                                                                            'overtime_fixed_allowance']:
                if entry.employee_id.contract_id.ot_wage == 'hourly_fixed':
                    entry.over_time = entry.duration * entry.employee_id.contract_id.hourly_ot_allowance

                if entry.employee_id.contract_id.ot_wage == 'daily_fixed':
                    overtime_rate = entry.employee_id.contract_id.over_time
                    working_hours = entry.employee_id.resource_calendar_id.hours_per_day
                    overtime_hours = entry.duration
                    entry.over_time = (overtime_rate / working_hours) * overtime_hours

            # entry.over_time = 0.0  # Default
            #
            # employee = entry.employee_id
            # if not employee:
            #     continue
            #
            # contract = employee.contract_id
            # if not contract:
            #     continue  # Skip if no contract
            #
            # hours_per_day = employee.sudo().resource_calendar_id.hours_per_day or 8.0  # fallback
            #
            # # --- Case 1: Regular Overtime ---
            # if entry.type_entry == 'overtime':
            #     overtime_rate = contract.over_time or 0.0
            #     if overtime_rate:
            #         entry.over_time = round(overtime_rate * entry.duration, 2)
            #     else:
            #         entry.over_time = 0
            #
            # elif entry.type_entry == 'overtime_fixed_allowance':
            #     if contract.is_fixed_allowance:
            #         fixed_amount = contract.fixed_allowance or 0.0
            #         if fixed_amount:
            #             total_fixed_allowance = (fixed_amount / hours_per_day) * entry.duration
            #             entry.over_time = round(total_fixed_allowance, 2)
            # else:
            #     entry.over_time = 0.0

    @api.depends('employee_id')
    def _compute_overtime_rate_deduction(self):
        """ To compute the total allowance of the employee """
        for entry in self:
            if entry.type_entry == 'overtime_fixed_allowance':
                employee = entry.employee_id
                hours_per_day = employee.sudo().resource_calendar_id.hours_per_day
                contract = employee.contract_id
                if contract:
                    over_time = contract.is_fixed_allowance
                    over_fixed_amount = contract.fixed_allowance
                    if over_time is None:
                        raise UserError(
                            f"{employee.name} does not have overtime allowances in their contract.")
                    total_fixed_allowance = 0
                    if over_time:
                        total_fixed_allowance += over_fixed_amount / hours_per_day * entry.duration
                    entry.over_time_rate = total_fixed_allowance
                else:
                    entry.over_time_rate = 0

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.start_date and record.end_date:
                if record.end_date <= record.start_date:
                    raise ValidationError("The End Date must be greater than the Start Date.")

    @api.depends('employee_id')
    def _compute_overseas_deduction(self):
        """ To compute the total allowance of the employee """
        for entry in self:
            entry.overseas_deduction = False
            if entry.type_entry == 'overseas_entries':
                employee = entry.employee_id
                contract = employee.contract_id
                if contract:
                    overseas_allowance = contract.overseas_allowance
                    if overseas_allowance is None:
                        raise UserError(
                            f"{employee.name} does not have overseas allowances in their contract.")
                    total_allowance = 0
                    if overseas_allowance:
                        total_allowance += overseas_allowance * entry.duration
                    entry.overseas_deduction = total_allowance
                else:
                    entry.overseas_deduction = 0

    @api.depends('employee_id')
    def _compute_anchorage_deduction(self):
        """ To compute the total allowance of the employee """
        for entry in self:
            entry.anchorage_deduction = False
            if entry.type_entry == 'anchorage_entry':
                employee = entry.employee_id
                contract = employee.contract_id
                if contract:
                    anchorage_allowance = contract.anchorage_allowance
                    if anchorage_allowance is None:
                        raise UserError(
                            f"{employee.name} does not have overseas or anchorage allowances in their contract.")
                    total_allowance = 0
                    if anchorage_allowance:
                        total_allowance += anchorage_allowance * entry.duration
                    entry.anchorage_deduction = total_allowance
                else:
                    entry.anchorage_deduction = 0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            employee = self.env['hr.employee'].browse(vals.get('employee_id'))
            if not employee.exists():
                raise UserError("Employee record not found!")
            if not employee.contract_id:
                raise UserError(f"You cannot create an entry for {employee.name} without a contract!")

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
                # entry.is_emp_entry_created == False

    # @api.onchange('start_date', 'end_date')
    # def get_duration(self):
    #     for entry in self:
    #         if entry.end_date and entry.start_date:
    #             days = (entry.end_date - entry.start_date).days + 1
    #             if days < 0:
    #                 days = 0
    #         else:
    #             days = 0
    #         entry.duration = days

    @api.onchange('start_date', 'end_date')
    def _onchange_dates(self):
        """ To make sure that the entries are made in the contract period itself """
        for entry in self:
            if entry.employee_id and entry.employee_id.contract_id:
                if entry.start_date and entry.start_date < entry.employee_id.contract_id.date_start:
                    raise ValidationError("The Entry Start Date cannot be before Employee Sign on!")
                if entry.end_date and entry.employee_id.contract_id.date_end and entry.end_date > entry.employee_id.contract_id.date_end:
                    raise ValidationError("The Entry End Date cannot be after Employee Sign off!")

    @api.model
    def _create_employee_entries(self):
        """ To update the Employee Entries """
        today = fields.Date.today()
        if today.day == 1:
            entries = self.env['hr.employee.entry'].search([('start_date', '=', today)])
            employees = self.env['hr.employee'].search([('crew', '=', True)])
            if not entries:
                for employee in employees:
                    vals = {
                        'employee_id': employee.id,
                        'start_date': today,
                    }
                    self.env['hr.employee.entry'].create(vals)
