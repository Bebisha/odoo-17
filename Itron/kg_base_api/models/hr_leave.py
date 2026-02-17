import ast
from datetime import datetime

import pytz

from odoo import models, fields, api
from odoo.tools import format_datetime
from datetime import datetime, time
import pytz
import ast
import logging

_logger = logging.getLogger(__name__)


class HrHoliday(models.Model):
    _inherit = "hr.leave"

    attach_ids = fields.Many2many(
        'ir.attachment', string="Attach File")

    timezone = fields.Char('Timezone')
    utc_time = fields.Char('UTC Time')

    @api.depends('leave_type_support_document', 'attachment_ids')
    def _compute_supported_attachment_ids(self):
        for holiday in self:
            holiday.supported_attachment_ids = holiday.attachment_ids + holiday.attach_ids
            holiday.supported_attachment_ids_count = len(holiday.attachment_ids.ids) + len(holiday.attach_ids)

    def _inverse_supported_attachment_ids(self):
        for holiday in self:
            holiday.attachment_ids = holiday.supported_attachment_ids

class HRAttendance(models.Model):
    _inherit='hr.attendance'

    in_mode= fields.Selection(
        selection_add=[('app', 'Biometric')],
    )

    out_mode = fields.Selection(
        selection_add=[('app', 'Biometric')],
    )

    def send_daily_attendance_email(self):
        today = datetime.today().date()

        company = self.env['res.company'].search([]).filtered(lambda x: x.country_code == 'IN')

        # ✅ Include all attendances with today's check-in
        attendances = self.env['hr.attendance'].sudo().search([
            ('check_in', '>=', datetime.combine(today, datetime.min.time())),
            ('check_in', '<=', datetime.combine(today, datetime.max.time())),
        ])

        filtered_attendances = attendances.filtered(lambda a: a.employee_id.company_id in company)

        if not filtered_attendances:
            return

        html_content = f"""
        <div>
            <p>Dear Sir,</p>
            <p>Please find below the daily attendance report for <strong>{today.strftime('%d %b %Y')}</strong>:</p>
            <table border="1" cellpadding="5" cellspacing="0">
                <tr>
                    <th>Employee</th>
                    <th>Check-In Time</th>
                    <th>Check-In Mode</th>
                    <th>Check-Out Time</th>
                    <th>Check-Out Mode</th>
                    <th>Hours Worked</th>
                </tr>
        """

        for rec in filtered_attendances:
            employee = rec.employee_id.name
            tz = pytz.timezone(rec.employee_id.tz or 'UTC')

            check_in_local = rec.check_in.astimezone(tz) if rec.check_in else None
            check_out_local = rec.check_out.astimezone(tz) if rec.check_out else None

            check_in = check_in_local.strftime('%I:%M %p') if check_in_local else '—'
            check_out = check_out_local.strftime('%I:%M %p') if check_out_local else '—'

            hours = (
                round((rec.check_out - rec.check_in).total_seconds() / 3600.0, 2)
                if rec.check_out else "—"
            )
            check_in_mode = dict(rec._fields['in_mode'].selection).get(rec.in_mode) or "N/A"

            if rec.check_out:
                check_out_mode = dict(rec._fields['out_mode'].selection).get(rec.out_mode) or "N/A"
            else:
                check_out_mode = "-"
            hours = int(rec.worked_hours)
            minutes = int(round((rec.worked_hours - hours) * 60))
            val = f"{hours:02d}:{minutes:02d}"

            html_content += f"""<tr>
                        <td>{employee}</td>
                        <td style="text-align:center">{check_in}</td>
                        <td style="text-align:center">{check_in_mode}</td>
                        <td style="text-align:center">{check_out}</td>
                        <td style="text-align:center">{check_out_mode}</td>
                        <td style='text-align:center'>{val}</td>
                    </tr>
                """

        html_content += """
            </table>
            <p>Best regards,<br/>Klystron Global</p>
        </div>
        """

        email_to = ''
        email_users_str = self.env['ir.config_parameter'].sudo().get_param('kg_base_api.report_users_ids')
        user_ids = ast.literal_eval(email_users_str)

        email_users = self.env['res.users'].browse(user_ids)
        if email_users:
            email_to = ','.join(user.login for user in email_users if user.login)

        self.env['mail.mail'].sudo().create({
            'subject': f"Daily Attendance Report - {today.strftime('%d %b %Y')}",
            'body_html': html_content,
            'email_to': email_to,
        }).send()

    @api.model
    def send_categorized_attendance_email(self):
        today = fields.Date.today()
        tz = pytz.timezone('Asia/Kolkata')

        email_users_str = self.env['ir.config_parameter'].sudo().get_param('kg_base_api.report_users_ids')
        if not email_users_str:
            return

        user_ids = ast.literal_eval(email_users_str)
        users = self.env['res.users'].browse(user_ids)
        email_to = ", ".join([user.partner_id.email for user in users if user.partner_id.email])

        approval_group = self.env.ref('kg_attendance.all_approval_access')

        employees = self.env['hr.employee'].search([
            ('user_id.groups_id', 'not in', approval_group.id),
        ])

        attendances = self.env['hr.attendance'].search([
            ('check_in', '>=', datetime.combine(today, time.min)),
            ('check_in', '<=', datetime.combine(today, time.max))
        ])

        leaves = self.env['hr.leave'].search([
            ('request_date_from', '<=', today),
            ('request_date_to', '>=', today)
        ])

        attendance_by_employee = {
            att.employee_id.id: att for att in attendances if att.employee_id in employees
        }

        on_time = []
        late_comers = []
        on_leave = []
        no_show = []

        for emp in employees:
            if emp.company_id.country_code != 'IN':
                continue

            emp_att = attendance_by_employee.get(emp.id)
            emp_leave = leaves.filtered(lambda l: l.employee_id.id == emp.id)

            # ✅ Add to leave table if on leave (even half-day)
            if emp_leave:
                for lv in emp_leave:
                    leave_type = 'Half Day' if lv.request_unit_half else 'Full Day'
                    half_day_type = ''
                    if lv.request_unit_half:
                        if lv.request_date_from_period == 'am':
                            half_day_type = ' - Morning'
                        elif lv.request_date_from_period == 'pm':
                            half_day_type = ' - Afternoon'
                    duration_display = f"{leave_type}{half_day_type}"

                    row = (
                        emp.name,
                        emp.department_id.name or '',
                        duration_display
                    )
                    on_leave.append(row)

            # ✅ Also add to On Time or Late if checked in
            if emp_att:
                emp_tz = pytz.timezone(emp.tz or 'Asia/Kolkata')
                check_in_local = emp_att.check_in.astimezone(emp_tz)
                check_in_str = check_in_local.strftime('%I:%M %p')
                check_in_time = check_in_local.time()
                check_in_mode = dict(emp_att._fields['in_mode']._description_selection(emp_att.env))[emp_att.in_mode]

                row = (
                    emp.name,
                    emp.department_id.name or '',
                    check_in_str,
                    check_in_mode,
                )

                calendar = emp.resource_calendar_id
                if calendar:
                    weekday = today.weekday()  # Monday=0
                    attendances = calendar.attendance_ids.filtered(
                        lambda a: int(a.dayofweek) == weekday
                    )

                    if attendances:
                        # Earliest start of today
                        earliest_attendance = min(attendances, key=lambda a: a.hour_from)
                        start_hour = int(earliest_attendance.hour_from)
                        start_minute = int((earliest_attendance.hour_from % 1) * 60)
                        work_start_time = time(start_hour, start_minute)

                        if check_in_time <= work_start_time:
                            on_time.append(row)
                        else:
                            late_comers.append(row)
                    else:
                        # No working hours for today → treat as no-show if not on leave
                        if not emp_leave:
                            no_show.append((emp.name, emp.department_id.name or ''))
                else:
                    # ❗ No calendar at all → treat as no-show if not on leave
                    if not emp_leave:
                        no_show.append((emp.name, emp.department_id.name or ''))
            elif not emp_leave:
                # ❗ Only if not on leave and not checked in
                no_show.append((emp.name, emp.department_id.name or ''))

        # Sort check-ins by time
        on_time.sort(key=lambda x: x[2])
        late_comers.sort(key=lambda x: x[2])

        def generate_table(title, headers, rows):
            if not rows:
                return f"<h3 style='margin-top:20px;'>{title}</h3><p>No employees</p>"

            table_html = f"<h3 style='margin-top:20px;'>{title}</h3><table border='1' cellpadding='6' cellspacing='0' style='border-collapse: collapse; width: 100%; font-size: 14px;'>"
            table_html += "<thead><tr>"
            for head in headers:
                table_html += f"<th style='background-color:#f2f2f2; text-align:left;'>{head}</th>"
            table_html += "</tr></thead><tbody>"
            for row in rows:
                table_html += "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
            table_html += "</tbody></table>"
            return table_html

        on_time_table = generate_table(
            "✅ On Time Employees (Based on Work Schedule)",
            ["Name", "Department", "Check-in Time", "Check-in Mode"],
            on_time
        )

        late_comers_table = generate_table(
            "⏰ Late Comers (Based on Work Schedule)",
            ["Name", "Department", "Check-in Time", "Check-in Mode"],
            late_comers
        )

        on_leave_table = generate_table(
            "On Leave ",
            ["Name", "Department", "Leave Type"],
            on_leave
        )

        no_show_table = generate_table(
            "🚫 No Show (No Check-in, No Leave or No Work Schedule)",
            ["Name", "Department"],
            no_show
        )
        formatted_date = today.strftime('%-d %b %Y %A')
        body_html = f"""
            <div style="font-family: Arial, sans-serif;">
                <h2>📋 Daily Attendance Report - {formatted_date}</h2>
                {on_time_table}
                {late_comers_table}
                {on_leave_table}
                {no_show_table}
                <p style='margin-top:20px;'>Regards,<br/>Klystron Global</p>
            </div>
            """

        mail_values = {
            'subject': f"Attendance Report - {today.strftime('%d-%m-%Y')}",
            'email_to': email_to,
            'body_html': body_html,
            'auto_delete': False,
            'email_from': self.env.user.company_id.email or self.env.user.email or 'noreply@example.com',
        }
        self.env['mail.mail'].create(mail_values).send()

class HRLateRequest(models.Model):
    _inherit= 'early.late.request'


    is_app = fields.Boolean('App Through')

