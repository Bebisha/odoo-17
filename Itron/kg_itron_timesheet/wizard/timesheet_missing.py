from datetime import timedelta
from odoo import api, fields, models,_
from odoo.exceptions import ValidationError


class MissingTimesheetWizard(models.Model):
    _name = 'timesheet.missing'

    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    # assignees_ids = fields.Many2many('hr.employee', string="Assignee", domain=[('is_need_timesheet', '=', False)])
    # assignee_ids = fields.Many2many('hr.employee', string="Assignees",
    #                               domain=[('contract_ids.state', '=', 'open'), ('is_need_timesheet', '=', False)])

    assignees_ids = fields.Many2many(
        'hr.employee',
        string="Assignee",
        domain=[('is_need_timesheet', '=', False)],
        relation="timesheet_missing_assignees_rel"
    )
    assignee_ids = fields.Many2many(
        'hr.employee',
        string="Assignees",
        domain=[('contract_ids.state', '=', 'open'), ('is_need_timesheet', '=', False)],
        relation="timesheet_missing_assignee_rel"
    )

    missing_ids = fields.One2many('missing.line', 'wizard_id', string="Line Ids")
    missing_time_ids = fields.One2many('missing.time.line', 'wizards_id', string="Missing Times")
    is_contract = fields.Boolean(string="Contract", default=False)



    @api.onchange('start_date', 'end_date', 'assignee_ids')
    def _onchange_dates(self):
        self.missing_ids = [(5, 0, 0)]  # Clear previous results
        if self.start_date and self.end_date:
            self._fetch_missing_timesheets()

    def _fetch_missing_timesheets(self):
        date_range = self._get_date_range(self.start_date, self.end_date)
        missing_by_date = {}
        timesheet_domain = [
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date),
        ]
        if self.assignee_ids:
            timesheet_domain.append(('employee_id', '=', self.assignee_ids.ids))
        timesheets = self.env['account.analytic.line'].search(timesheet_domain)
        timesheet_dict = {}
        for ts in timesheets:
            if ts.employee_id.id not in timesheet_dict:
                timesheet_dict[ts.employee_id.id] = set()
            timesheet_dict[ts.employee_id.id].add(ts.date)
        employee_domain = []
        if self.assignee_ids:
            employee_domain.append(('id', '=', self.assignee_ids.ids))

        employees = self.env['hr.employee'].search(employee_domain)

        leave_domain = [
            ('employee_id', 'in', employees.ids),
            ('request_date_from', '<=', self.end_date),
            ('request_date_to', '>=', self.start_date),
            ('state', 'in', ['confirm', 'validate'])
        ]
        leaves = self.env['hr.leave'].search(leave_domain)

        leave_dict = {}
        for leave in leaves:
            if leave.employee_id.id not in leave_dict:
                leave_dict[leave.employee_id.id] = set()
            leave_dates = self._get_date_range(leave.request_date_from, leave.request_date_to)
            leave_dict[leave.employee_id.id].update(leave_dates)

        for employee in employees:
            contracts = self.env['hr.contract'].search([
                ('employee_id', '=', employee.id),
                ('state', '=', 'open')
            ])

            working_days = set()
            for contract in contracts:
                if contract.resource_calendar_id:
                    dayofweek = contract.resource_calendar_id.attendance_ids.mapped('dayofweek')
                    int_list = [int(num) for num in dayofweek]
                    unique_sorted_list = sorted(set(int_list))
                    for single_date in date_range:
                        if single_date.weekday() in unique_sorted_list:
                            working_days.add(single_date)

            # Group missing timesheets by date, excluding leave dates
            sorted_dates = sorted(working_days)
            for single_date in sorted_dates:
                if (employee.id not in timesheet_dict or single_date not in timesheet_dict[employee.id]) and \
                        (employee.id not in leave_dict or single_date not in leave_dict[employee.id]):
                    if single_date not in missing_by_date:
                        missing_by_date[single_date] = []
                    missing_by_date[single_date].append({
                        'employee_id': employee.id,
                        'missing_date': single_date,
                    })

        missing_employees = []
        for date in sorted(missing_by_date):
            for employee_data in missing_by_date[date]:
                missing_employees.append((0, 0, employee_data))

        self.missing_ids = missing_employees

    def _get_date_range(self, start_date, end_date):
        delta = end_date - start_date
        return [start_date + timedelta(days=i) for i in range(delta.days + 1)]

    @api.onchange('start_date', 'end_date', 'assignees_ids', 'is_contract')
    def _onchange_datess(self):
        print(f"Start Date: {self.start_date}, End Date: {self.end_date}, Assignees ID: {self.assignees_ids}")
        if not self.is_contract:
            self.missing_time_ids = [(5, 0, 0)]

            if self.start_date and self.end_date:
                self._fetch_missing_time_sheetss()

    def _fetch_missing_time_sheetss(self):
        # Get the date range between start_date and end_date
        date_range = self._get_date_time_range(self.start_date, self.end_date)
        print(date_range, "Date Range for Timesheet Check")

        # Define the domain for fetching timesheets within the date range and specific employee
        timesheet_domain = [
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date),
        ]
        if self.assignees_ids:
            timesheet_domain.append(('employee_id', '=', self.assignees_ids.ids))

        # Fetch timesheets that match the date range and, optionally, the specified employee
        timesheets = self.env['account.analytic.line'].search(timesheet_domain)
        print("Timesheet Domain:", timesheet_domain)

        timesheet_dict = {}
        for ts in timesheets:
            if ts.date not in timesheet_dict:
                timesheet_dict[ts.date] = set()
            timesheet_dict[ts.date].add(ts.employee_id.id)
        print("Timesheet Dictionary:", timesheet_dict)

        # Fetch employees based on assignees_id or all employees
        employee_domain = []
        if self.assignees_ids:
            employee_domain.append(('id', '=', self.assignees_ids.ids))

        employees = self.env['hr.employee'].search(employee_domain)
        employee_ids = employees.mapped('id')
        leave_domain = [
            ('employee_id', 'in', employees.ids),
            ('request_date_from', '<=', self.end_date),
            ('request_date_to', '>=', self.start_date),
            ('state', 'in', ['confirm', 'validate'])
        ]
        leaves = self.env['hr.leave'].search(leave_domain)
        print(leaves, "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVV")
        leave_dict = {}
        for leave in leaves:
            if leave.employee_id.id not in leave_dict:
                print(leave.employee_id.id, "BBBBBBBBBBBB")
                leave_dict[leave.employee_id.id] = set()
            leave_dates = self._get_date_time_range(leave.request_date_from, leave.request_date_to)
            leave_dict[leave.employee_id.id].update(leave_dates)

        print(leave_dict, "CCCCCCCCCCCCCCCCCCccccccccccc")

        # Collect missing timesheet entries
        missing_records = []
        for date in date_range:
            if date.weekday() >= 5:
                continue
            for employee in employees:
                if not employee.is_need_timesheet:
                    # Check if the employee has a timesheet for this date
                    if employee.id not in timesheet_dict.get(date, set()):
                        if date in leave_dict.get(employee.id, set()):
                            continue
                        missing_records.append({
                            'missing_date': date,
                            'employee_id': employee.id,
                            'wizards_id': self.id,
                        })

        # Update missing_time_ids with missing records in-memory (without database commit)
        self.missing_time_ids = [(0, 0, record) for record in missing_records]


    def _get_date_time_range(self, start_date, end_date):
        """Return a list of dates between start_date and end_date inclusive."""
        delta = end_date - start_date
        return [start_date + timedelta(days=i) for i in range(delta.days + 1)]


class MissingLine(models.Model):
    _name = 'missing.line'

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    missing_date = fields.Date(string="Missing Date", required=True)
    wizard_id = fields.Many2one('timesheet.missing', string="Wizard Reference")


class MissingTimeLine(models.Model):
    _name = 'missing.time.line'

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    missing_date = fields.Date(string="Missing Date", required=True)
    wizards_id = fields.Many2one('timesheet.missing', string="Wizard Reference")

#
# from datetime import timedelta
#
# from odoo import api, fields, models, _
#
#
# class MissingTimesheetWizard(models.Model):
#     _name = 'timesheet.missing'
#
#     start_date = fields.Date(string="Start Date")
#     end_date = fields.Date(string="End Date")
#     assignee_id = fields.Many2one('hr.employee',string="Assignees")
#     missing_ids = fields.One2many('missing.line','wizard_id',string="Line Ids")
#
#     @api.onchange('start_date', 'end_date', 'assignee_id')
#     def _onchange_dates(self):
#         self.missing_ids = [(5, 0, 0)]  # Clear previous results
#         if self.start_date and self.end_date:
#             self._fetch_missing_timesheets()
#
#     def _fetch_missing_timesheets(self):
#         date_range = self._get_date_range(self.start_date, self.end_date)
#         missing_by_date = {}  # Dictionary to group missing employees by date
#
#         # Build the domain for timesheets, considering the assignee_id if provided
#         timesheet_domain = [
#             ('date', '>=', self.start_date),
#             ('date', '<=', self.end_date),
#         ]
#         if self.assignee_id:
#             timesheet_domain.append(('employee_id', '=', self.assignee_id.id))
#
#         # Fetch all timesheets based on the domain
#         timesheets = self.env['account.analytic.line'].search(timesheet_domain)
#
#         # Create a dictionary of timesheet dates by employee
#         timesheet_dict = {}
#         for ts in timesheets:
#             if ts.employee_id.id not in timesheet_dict:
#                 timesheet_dict[ts.employee_id.id] = set()
#             timesheet_dict[ts.employee_id.id].add(ts.date)
#
#         # Build the domain for employees, considering the assignee_id if provided
#         employee_domain = []
#         if self.assignee_id:
#             employee_domain.append(('id', '=', self.assignee_id.id))
#
#         employees = self.env['hr.employee'].search(employee_domain)
#
#         for employee in employees:
#             contracts = self.env['hr.contract'].search([
#                 ('employee_id', '=', employee.id),
#                 ('state', '=', 'open')
#             ])
#
#             working_days = set()
#             for contract in contracts:
#                 if contract.resource_calendar_id:
#                     dayofweek = contract.resource_calendar_id.attendance_ids.mapped('dayofweek')
#                     int_list = [int(num) for num in dayofweek]
#                     unique_sorted_list = sorted(set(int_list))
#                     for single_date in date_range:
#                         if single_date.weekday() in unique_sorted_list:
#                             working_days.add(single_date)
#
#             # Group missing timesheets by date
#             sorted_dates = sorted(working_days)
#             for single_date in sorted_dates:
#                 if employee.id not in timesheet_dict or single_date not in timesheet_dict[employee.id]:
#                     if single_date not in missing_by_date:
#                         missing_by_date[single_date] = []
#                     missing_by_date[single_date].append({
#                         'employee_id': employee.id,
#                         'missing_date': single_date,
#                     })
#
#         # Flatten the result to list of tuples
#         missing_employees = []
#         for date in sorted(missing_by_date):
#             for employee_data in missing_by_date[date]:
#                 missing_employees.append((0, 0, employee_data))
#
#         self.missing_ids = missing_employees
#
#     def _get_date_range(self, start_date, end_date):
#         delta = end_date - start_date
#         return [start_date + timedelta(days=i) for i in range(delta.days + 1)]
#
# class MissingLine(models.Model):
#     _name = 'missing.line'
#     # _order = 'missing_date'
#
#     employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
#     missing_date = fields.Date(string="Missing Date", required=True)
#     on_leave = fields.Selection([
#         ('no', 'No'), ('yes', 'Yes')],string="Leave")
#     wizard_id = fields.Many2one('timesheet.missing', string="Wizard Reference")


# @api.onchange('start_date', 'end_date', 'assignees_id', 'is_contract')
# def _onchange_datess(self):
#     print(f"Start Date: {self.start_date}, End Date: {self.end_date}, Assignees ID: {self.assignees_id}")
#     if not self.is_contract:
#         print(self.missing_time_ids, "missing_time_ids")
#         self.missing_time_ids = [(5, 0, 0)]
#
#         if self.start_date and self.end_date:
#             self._fetch_missing_time_sheetss()
#
# def _fetch_missing_time_sheetss(self):
#     date_range = self._get_date_time_range(self.start_date, self.end_date)
#     print(date_range, "llllllllllllllllll")
#
#     timesheet_domain = [
#         ('date', '>=', self.start_date),
#         ('date', '<=', self.end_date),
#     ]
#     if self.assignees_id:
#         timesheet_domain.append(('employee_id', '=', self.assignees_id.id))
#
#     print(timesheet_domain, "DDDDDDDDDDDDDdd")
#
#     timesheets = self.env['account.analytic.line'].search(timesheet_domain)
#     print(timesheets, "timesheets")
#
#     timesheet_dict = {}
#     for ts in timesheets:
#         print(ts, "TTTTTTTTTTTTTTTTTTTTTTT")
#         if ts.employee_id.id not in timesheet_dict:
#             timesheet_dict[ts.employee_id.id] = set()
#         timesheet_dict[ts.employee_id.id].add(ts.date)
#
#     employee_domain = []
#     if self.assignees_id:
#         employee_domain.append(('id', '=', self.assignees_id.id))
#
#     employees = self.env['hr.employee'].search(employee_domain)
#
#     missing_records = []
#     for employee in employees:
#         for date in date_range:
#             if date not in timesheet_dict.get(employee.id, set()):
#                 week_off_reason = "Week Off" if date.weekday() >= 5 else ""
#                 missing_records.append({
#                     'employee_id': employee.id,
#                     'missing_date': date,
#                     'reason': week_off_reason,
#                     'wizards_id': self.id,
#                 })
#     self.missing_time_ids = [(0, 0, record) for record in missing_records]
#
# def _get_date_time_range(self, start_date, end_date):
#     """Return a list of dates between start_date and end_date inclusive"""
#     delta = end_date - start_date
#     return [start_date + timedelta(days=i) for i in range(delta.days + 1)]
