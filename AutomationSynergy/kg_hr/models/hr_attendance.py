import datetime
from datetime import datetime, time
import pytz
from odoo.tools import float_compare, DEFAULT_SERVER_DATETIME_FORMAT

from odoo import fields, models, api, _


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    ot_hours = fields.Float('OT Hours', default=0.00, compute='compute_ot_hours')
    normal_hours = fields.Float(string="Normal Hours", default=0.00, compute='compute_normal_hours')


    @api.depends('normal_hours', 'worked_hours')
    def compute_ot_hours(self):
        for rec in self:
            rec.ot_hours = False
            if rec.normal_hours <= rec.worked_hours:
                rec.ot_hours = rec.worked_hours - rec.normal_hours

    # overtime_hrs = fields.Float('Overtime Hrs')

    @api.depends('check_in', 'check_out', 'employee_id')
    def compute_normal_hours(self):
        for rec in self:
            rec.normal_hours = 0.0
            user_tz = self.env.user.tz or 'UTC'
            local = pytz.timezone(user_tz)

            if rec.check_in and rec.check_out:
                # Convert check_in and check_out to local time
                check_in_local = rec.check_in.astimezone(local)
                check_out_local = rec.check_out.astimezone(local)

                # Extract the date part
                check_in_date = check_in_local.date()
                check_out_date = check_out_local.date()

                # Define the end of the normal working day as 6:30 PM
                normal_end_time = datetime.combine(check_out_date, time(18, 30))
                normal_end_time = local.localize(normal_end_time)
                if check_in_date == check_out_date:
                    normal_worked_time = normal_end_time - check_in_local
                    normal_hours = normal_worked_time.total_seconds() / 3600.0
                    rec.normal_hours = normal_hours
