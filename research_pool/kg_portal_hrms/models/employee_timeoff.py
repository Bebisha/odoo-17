from odoo import models, fields


class TimeOff(models.Model):
    _name = 'employee.time_off'
    _description = 'Time Off Request'

    employee_id = fields.Char(string='Employee ID', required=True)
    # state = fields.Selection([
    #     ('draft', 'To Submit'),
    #     ('posted', 'Open'),
    #     ('cancel', 'Cancelled')
    # ], string='Invoice Status', readonly=True)
    holiday_status_id = fields.Char(string='Time Off Type', required=True)
    number_of_days_display = fields.Char(string='Duration', required=True)
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    reason = fields.Text(string='Description', required=True)
