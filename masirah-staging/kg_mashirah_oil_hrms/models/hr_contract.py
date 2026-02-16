from datetime import timedelta

from odoo import models, fields, api


class KGHRContractInherit(models.Model):
    _inherit = "hr.contract"

    ticket_flight_allowance = fields.Monetary(string="Flight Ticket")
    hotel_allowance = fields.Monetary(string="Hotel")
    last_notification_date = fields.Date("Last Notification Date")
    total_salary = fields.Monetary(string="Total Salary")
    housing_allowance = fields.Monetary(string="Housing Allowance")
    transport_allowance = fields.Monetary(string="Transport Allowance")
    utilities_allowance = fields.Monetary(string="Utilities Allowance")
    offshore_allowance = fields.Monetary(string="Offshore Allowance", default=75)
    other_allowance = fields.Monetary(string="Other Allowance")
    c2c_month = fields.Monetary(string="Month Wage", compute="compute_c2c_wage")
    c2c_year = fields.Monetary(string="Year Wage", compute="compute_c2c_wage")

    @api.depends('wage', 'housing_allowance', 'transport_allowance', 'utilities_allowance', 'other_allowance')
    def compute_c2c_wage(self):
        for rec in self:
            rec.c2c_month = rec.wage + rec.hotel_allowance + rec.transport_allowance + rec.utilities_allowance + rec.other_allowance
            rec.c2c_year = rec.c2c_month * 12

    @api.depends('total_salary')
    def compute_ot_hour_day(self):
        for rec in self:
            if rec.total_salary:
                rec.over_day = rec.total_salary * 12 / 365
                if rec.over_day:
                    rec.over_hour = rec.over_day / 8
                else:
                    rec.over_hour = 0.00
            else:
                rec.over_day = 0.00
                rec.over_hour = 0.00

    def send_expiry_notification(self):
        current_date = fields.Date.today()
        next_month_date = current_date + timedelta(days=30)
        contracts_to_notify = self.search([
            ('date_end', '>', current_date),
            ('date_end', '=', next_month_date),
            '|', ('last_notification_date', '=', False), ('last_notification_date', '<', current_date),
        ])

        for contract in contracts_to_notify:
            # For example, sending an email notification to the employee
            email_values = {'email_to': contract.employee_id.work_email}

            template_id = self.env.ref('kg_mashirah_oil_hrms.expiry_notification_mail')
            template_id.send_mail(contract.id, force_send=True, email_values=email_values)

            contract.write({'last_notification_date': current_date})

    @api.model
    def send_expiry_notifications_cron(self):
        self.send_expiry_notification()
