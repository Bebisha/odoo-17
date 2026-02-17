# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class EmployeeEntryWizard(models.TransientModel):
    _name = 'employee.entry.wizard'
    _description = 'employee.entry.wizard'

    employee_ids = fields.Many2many('hr.employee', string='Employees')
    start_date = fields.Date(String='Start Date')
    end_date = fields.Date(String='End Date')
    vessel_id = fields.Many2one('sponsor.sponsor', string='Vessel')

    def default_get(self, fields):
        """ Listing all crew members coming under logged in factory manager """
        res = super(EmployeeEntryWizard, self).default_get(fields)
        employees = self.env['hr.employee'].search(
            [('crew', '=', True), ('factory_manager_ids.user_id', '=', self.env.user.id)])
        res['employee_ids'] = [(6, 0, employees.ids)]
        return res

    def action_create_entries(self):
        """ Button action to create Employee Entries """
        if not self.employee_ids:
            raise ValidationError("The Employees field is empty. Kindly select at least one employee to proceed.")

        if not self.start_date:
            raise ValidationError("Please select the Start Date")

        if not self.end_date:
            raise ValidationError("Please select the End Date")

        employees = self.employee_ids

        for employee in employees:
            base_domain = [
                ('employee_id', '=', employee.id),
                '|',
                ('date_end', '=', False),
                ('date_end', '>=', self.start_date),
                ('date_start', '<=', self.end_date),
            ]

            if self.vessel_id:
                base_domain.append(('sponsor_name', '=', self.vessel_id.id))

            crew_transfer_contracts = self.env['hr.contract'].search(base_domain)

            if crew_transfer_contracts:
                for contract in crew_transfer_contracts:
                    if not contract.date_end:
                        date_end = self.end_date
                    elif contract.date_end and contract.date_end >= self.end_date:
                        date_end = self.end_date
                    elif contract.date_end and contract.date_end <= self.end_date:
                        date_end = contract.date_end
                    else:
                        date_end = False

                    if contract.date_start and contract.date_start <= self.start_date:
                        date_start = self.start_date
                    elif contract.date_start and contract.date_start >= self.start_date:
                        date_start = contract.date_start
                    else:
                        date_start = False

                    vals = {
                        'employee_id': employee.id,
                        'vessels_id': contract.sponsor_name.id,
                        'start_date': date_start,
                        'end_date': date_end,
                    }
                    self.env['hr.employee.entry'].create(vals)

    def action_create_entries_previous_month_data(self):
        """ Button action to create Employee Entries from previous month data """

        today = fields.date.today()
        first_day_of_current_month = today.replace(day=1)
        last_day_previous_month = first_day_of_current_month - timedelta(days=1)
        first_day_previous_month = last_day_previous_month.replace(day=1)

        if today.month == 12:
            first_day_next_month = today.replace(year=today.year + 1, month=1, day=1)
        else:
            first_day_next_month = today.replace(month=today.month + 1, day=1)

        last_day_of_current_month = first_day_next_month - timedelta(days=1)

        previous_entries_ids = self.env['hr.employee.entry'].search(
            [('start_date', '>=', first_day_previous_month), ('start_date', '<=', last_day_previous_month)])

        employee_ids = previous_entries_ids.mapped('employee_id')

        if employee_ids:
            for employee in employee_ids:
                if employee.employee_status == 'active':
                    base_domain = [
                        ('employee_id', '=', employee.id),
                        '|',
                        ('date_end', '=', False),
                        ('date_end', '>=', first_day_of_current_month),
                        ('date_start', '<=', last_day_of_current_month),
                    ]

                    if self.vessel_id:
                        base_domain.append(('sponsor_name', '=', self.vessel_id.id))

                    crew_transfer_contracts = self.env['hr.contract'].search(base_domain)

                    if crew_transfer_contracts:
                        for contract in crew_transfer_contracts:
                            if not contract.date_end:
                                date_end = last_day_of_current_month
                            elif contract.date_end and contract.date_end >= last_day_of_current_month:
                                date_end = last_day_of_current_month
                            elif contract.date_end and contract.date_end <= last_day_of_current_month:
                                date_end = contract.date_end
                            else:
                                date_end = False

                            if contract.date_start and contract.date_start <= first_day_of_current_month:
                                date_start = first_day_of_current_month
                            elif contract.date_start and contract.date_start >= first_day_of_current_month:
                                date_start = contract.date_start
                            else:
                                date_start = False

                            vals = {
                                'employee_id': employee.id,
                                'vessels_id': contract.sponsor_name.id,
                                'start_date': date_start,
                                'end_date': date_end,
                            }
                            self.env['hr.employee.entry'].create(vals)

        # def action_create_entries_previous_month_data(self):
        #     """ Button action to create Employee Entries from previous month data """
        #     today = datetime.today()
        #     first_day_of_current_month = self.start_date.replace(day=1)
        #     last_day_of_previous_month = first_day_of_current_month - timedelta(days=1)
        #     first_day_of_previous_month = last_day_of_previous_month.replace(day=1)
        #     if first_day_of_current_month.month == 12:
        #         first_day_of_next_month = first_day_of_current_month.replace(year=first_day_of_current_month.year + 1,
        #                                                                      month=1, day=1)
        #     else:
        #         first_day_of_next_month = first_day_of_current_month.replace(month=first_day_of_current_month.month + 1,
        #                                                                      day=1)
        #     last_day_of_current_month = first_day_of_next_month - timedelta(days=1)
        #
        #     if self.vessel_id:
        #         entry_employees = self.env['hr.employee.entry'].search([
        #             ('vessels_id', '=', self.vessel_id.id),
        #             ('start_date', '>=', first_day_of_previous_month),
        #             ('end_date', '<=', last_day_of_previous_month)
        #         ]).mapped('employee_id')
        #         sign_off_employees = self.env['sign.on.off'].search([
        #             ('vessel_id', '=', self.vessel_id.id),
        #             '|', '|',
        #             ('sign_off', '>=', first_day_of_current_month),
        #             ('sign_off', '<=', last_day_of_current_month),
        #             ('sign_off', '=', False)
        #         ]).mapped('employee_id')
        #     else:
        #         entry_employees = self.env['hr.employee.entry'].search([
        #             ('start_date', '>=', first_day_of_previous_month),
        #             ('end_date', '<=', last_day_of_previous_month)
        #         ]).mapped('employee_id')
        #
        #         sign_off_employees = self.env['sign.on.off'].search([
        #             '|', '|',
        #             ('sign_off', '>=', first_day_of_current_month),
        #             ('sign_off', '<=', last_day_of_current_month),
        #             ('sign_off', '=', False)
        #         ]).mapped('employee_id')
        #
        #     # to find crew if in between crew transfer is there
        #
        #     crew_transfer_lines = self.env['crew.transfer'].search([
        #         ('date_transfer', '>=', first_day_of_current_month),
        #         ('date_transfer', '<=', last_day_of_current_month)
        #     ]).mapped('crew_transfer_line_ids')
        #
        #     employees = entry_employees | sign_off_employees
        #
        #     employees_with_contract = employees.filtered(
        #         lambda emp: emp.contract_id and (
        #                 emp.contract_id.date_end is False or
        #                 (emp.contract_id.date_end and emp.contract_id.date_end >= first_day_of_current_month)
        #         )
        #     )
        #
        #     for employee in employees_with_contract:
        #         employee_entries = self.env['hr.employee.entry'].search([
        #             ('employee_id', '=', employee.id),
        #             ('start_date', '>=', first_day_of_previous_month),
        #             ('end_date', '<=', last_day_of_previous_month)
        #         ])
        #
        #         over_time = sum(employee_entries.mapped('over_time'))
        #         holiday_allowance = sum(employee_entries.mapped('holiday_allowance'))
        #         bonus = sum(employee_entries.mapped('bonus'))
        #         penalty = sum(employee_entries.mapped('penalty'))
        #
        #         if self.end_date and employee.contract_id.date_end and employee.contract_id.date_end > last_day_of_current_month:
        #             end_date = self.end_date
        #         elif employee.contract_id.date_end and employee.contract_id.date_end > last_day_of_current_month:
        #             end_date = last_day_of_current_month
        #         elif employee.contract_id.date_end:
        #             end_date = employee.contract_id.date_end
        #         elif not employee.contract_id.date_end and not self.end_date:
        #             end_date = last_day_of_current_month
        #         else:
        #             end_date = self.end_date
        #
        #         transfer_found = False
        #
        #         for line in crew_transfer_lines:
        #             if employee == line.employee_id:
        #                 transfer_found = True
        #                 transfer_date = line.date_transfer
        #                 old_vessel = line.crew_transfer_id.old_vessel_id
        #                 new_vessel = line.crew_transfer_id.new_vessel_id
        #
        #                 self.env['hr.employee.entry'].create({
        #                     'employee_id': employee.id,
        #                     'vessels_id': old_vessel.id if old_vessel else False,
        #                     'start_date': self.start_date or first_day_of_current_month,
        #                     'end_date': transfer_date - timedelta(days=1),
        #                 })
        #
        #                 self.env['hr.employee.entry'].create({
        #                     'employee_id': employee.id,
        #                     'vessels_id': new_vessel.id if new_vessel else False,
        #                     'start_date': transfer_date,
        #                     'end_date': end_date,
        #                 })
        #                 break
        #
        #         if not transfer_found:
        #             print(employee.name, employee.sponsor_name.name, 'llllllllllllllllllllllllllllll')
        #             self.env['hr.employee.entry'].create({
        #                 'employee_id': employee.id,
        #                 'vessels_id': self.vessel_id.id if self.vessel_id else employee.sponsor_name.id,
        #                 'start_date': self.start_date or first_day_of_current_month,
        #                 'end_date': end_date,
        #             })

    def action_create_entries_from_sign_on_off(self):
        """Create employee entries from sign-on/off within selected period"""

        self.ensure_one()

        if self.start_date >= self.end_date:
            raise UserError(_("From Date must be earlier than To Date"))

        sign_records = self.env['sign.on.off'].search([
            ('sign_on', '<=', self.end_date), '|',
            ('sign_off', '>=', self.start_date),
            ('sign_off', '=', False),
        ])

        if not sign_records:
            raise UserError(_("No signed-on employees found for the selected period."))

        employee_entry_obj = self.env['hr.employee.entry']
        created_entries = []

        for sign in sign_records:

            # existing_entry = employee_entry_obj.search([
            #     ('employee_id', '=', sign.employee_id.id),
            #     ('date', '=', fields.Date.date_to(sign.sign_on)),
            # ], limit=1)
            #
            # if existing_entry:
            #     continue

            vals = {
                'employee_id': sign.employee_id.id,
                'start_date': self.start_date,
                'end_date': self.end_date,
            }

            created_entries.append(employee_entry_obj.create(vals))

        if not created_entries:
            raise UserError(_("Entries already exist for all signed-in employees."))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('%s employee entries created successfully.') % len(created_entries),
                'sticky': False,
                'next': {
                    'type': 'ir.actions.act_window_close',
                },
            }
        }
