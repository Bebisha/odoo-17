from odoo import models, fields, api, _
from datetime import datetime, time, timedelta, date
import pytz
import re

from odoo.exceptions import ValidationError, UserError


class EarlyLateRequest(models.Model):
    _name = "early.late.request"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Early Late Request"

    company_name = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)
    name = fields.Char(string='Reference', required=True,
                       readonly=True, default=lambda self: _('New'))
    type = fields.Selection([('early_departure', 'Early Departure'), ('late_arrival', ' Late Arrival')],
                            string="Type",
                            default="late_arrival", required=True)
    date_late = fields.Date(string="Late In Time", default=fields.Date.today, )
    hours = fields.Selection(
        [(str(h), f"{h:02}") for h in range(0, 24)],
        string="Hours", required=True)
    minutes = fields.Selection(
        [(str(m), f"{m:02}") for m in range(0, 60, 1)],
        string="Minutes", required=True)
    time_string = fields.Char(string="Time", compute="_compute_time_string", store=True)

    @api.depends('hours', 'minutes', 'seconds')
    def _compute_time_string(self):
        for record in self:
            if record.hours and record.minutes:
                secs = record.seconds.zfill(2) if record.seconds else "00"
                record.time_string = f"{record.hours.zfill(2)}:{record.minutes.zfill(2)}:{secs}"
            else:
                record.time_string = False

    date_early = fields.Date(string="Early Going In", default=fields.Date.today)
    early_hrs = fields.Char(string="Early By", compute="compute_early_hrs")
    late_hrs = fields.Char(string="Late By", compute="compute_early_late_hrs")
    employee_id = fields.Many2one("hr.employee", string="Employee", required=True,
                                  default=lambda self: self._default_employee(),
                                  domain=lambda self: self._get_employee_domain())
    reason = fields.Char(string="Reason", required=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('request', 'Request Send'), ('lm_approved', 'Approved'),
         ('cancel', 'Return')],
        default='draft', tracking=True)
    is_readonly = fields.Boolean(string="Readonly", default=False)
    # late_id = fields.Many2one('late.report', 'Late Form')
    company_id = fields.Many2one('res.company', 'Company')
    display_type = fields.Selection(
        selection=[
            ('line_section', "Section"),
            ('line_note', "Note"),
        ],
        default=False)

    effective_date = fields.Date(string=" Date", compute="_compute_effective_date", store=True)
    confirm_date = fields.Datetime(string="Confirmation Date", tracking=True)
    reason_for_return = fields.Char(string="Reason For Return", copy=False)
    is_reason_editable = fields.Boolean(default=False, compute='compute_is_reason_editable')
    seconds = fields.Selection(
        [(str(m), f"{m:02}") for m in range(0, 60, 1)],
        string="Seconds", )

    def compute_is_reason_editable(self):
        for rec in self:
            rec.is_reason_editable = False
            rec.is_reason_editable = (
                        self.env.user.has_group('hr_holidays.group_hr_holidays_manager') or self.env.user.has_group(
                    'hr_holidays.group_hr_holidays_user'))

    @api.depends('type', 'date_late', 'date_early')
    def _compute_effective_date(self):
        for record in self:
            if record.type == 'early_departure':
                record.effective_date = record.date_early
                print(record.date_late, "ssfs")
            elif record.type == 'late_arrival':
                record.effective_date = record.date_late

    @api.model
    def _default_employee(self):
        user = self.env.user
        employee = self.env['hr.employee'].search([('user_id', '=', user.id), ('company_id', '=', self.env.company.id)],
                                                  limit=1)
        return employee.id

    @api.model
    def _get_employee_domain(self):
        user = self.env.user
        if user.has_group('base.group_system') or user.has_group(
                'hr_holidays.group_hr_holidays_manager'):  # Replace with the appropriate admin group if necessary
            return []  # Admin can see all employees
        else:
            # Regular users can only see their own employee record
            employee = self.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
            return [('id', '=', employee.id)]

    @api.model
    def create(self, vals):
        company = self.env['res.company'].browse(vals.get('company_name')).name
        if self.env['hr.employee'].browse(vals.get('employee_id')).is_check_employee:
            raise ValidationError(
                f"You can't create {dict(self._fields['type'].selection).get(vals.get('type'))} in {company}.")

        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'kg.early.req') or _('New')
        res = super(EarlyLateRequest, self).create(vals)
        return res

    @api.depends('hours', 'minutes', 'seconds', 'date_late')
    def compute_early_late_hrs(self):
        """Compute hours, minutes, and seconds of late coming based on the employee's scheduled start time."""
        for rec in self:
            rec.late_hrs = "0 hours, 0 minutes, 0 seconds"

            if rec.hours is not None and rec.minutes is not None and rec.date_late:
                employee = getattr(rec, 'employee_id', None)
                if not employee or not employee.resource_calendar_id:
                    rec.late_hrs = "No work schedule found"
                    continue

                # Find the weekday for the selected date
                weekday = rec.date_late.weekday()  # Monday=0

                # Filter attendances for that weekday
                attendances = employee.resource_calendar_id.attendance_ids.filtered(
                    lambda a: int(a.dayofweek) == weekday
                )

                # If no work schedule for that day → No lateness check
                if not attendances:
                    rec.late_hrs = "No work schedule for this day"
                    continue

                # Get earliest start time for that weekday
                earliest_attendance = min(attendances, key=lambda a: a.hour_from)
                start_hour = int(earliest_attendance.hour_from)
                start_minute = int((earliest_attendance.hour_from % 1) * 60)
                work_start_time = time(start_hour, start_minute)

                # Convert to datetime for comparison
                selected_hour = int(rec.hours)
                selected_minute = int(rec.minutes)
                selected_second = int(rec.seconds) if rec.seconds else 0
                selected_time = time(selected_hour, selected_minute, selected_second)

                selected_datetime = datetime.combine(rec.date_late, selected_time)
                target_datetime = datetime.combine(rec.date_late, work_start_time)

                # Compare
                if selected_datetime > target_datetime:
                    time_diff = selected_datetime - target_datetime
                    late_hours = time_diff.seconds // 3600
                    late_minutes = (time_diff.seconds % 3600) // 60
                    late_seconds = time_diff.seconds % 60
                    rec.late_hrs = f"{late_hours} hours, {late_minutes} minutes, {late_seconds} seconds"
                else:
                    rec.late_hrs = "0 hours, 0 minutes, 0 seconds"

    @api.depends('date_early', 'hours', 'minutes', 'seconds')
    def compute_early_hrs(self):
        """Compute hours, minutes, and seconds of early going
        based on employee's scheduled end time."""
        for rec in self:
            rec.early_hrs = "0 hours, 0 minutes, 0 seconds"

            if rec.date_early and rec.hours is not None and rec.minutes is not None:
                employee = getattr(rec, 'employee_id', None)
                if not employee or not employee.resource_calendar_id:
                    rec.early_hrs = "No work schedule found"
                    continue

                # Weekday for the selected date
                weekday = rec.date_early.weekday()  # Monday=0

                # Filter attendances for that weekday
                attendances = employee.resource_calendar_id.attendance_ids.filtered(
                    lambda a: int(a.dayofweek) == weekday
                )

                if not attendances:
                    rec.early_hrs = "No work schedule for this day"
                    continue

                # Get latest scheduled end time
                latest_attendance = max(attendances, key=lambda a: a.hour_to)
                end_hour = int(latest_attendance.hour_to)
                end_minute = int((latest_attendance.hour_to % 1) * 60)
                work_end_time = time(end_hour, end_minute)

                # Take seconds, default 0
                sec = rec.seconds if rec.seconds is not None else 0

                # Convert to datetime for comparison
                leaving_time = time(int(rec.hours), int(rec.minutes), int(sec))
                leaving_datetime = datetime.combine(rec.date_early, leaving_time)
                target_datetime = datetime.combine(rec.date_early, work_end_time)

                # Compare
                if leaving_datetime < target_datetime:
                    time_diff = target_datetime - leaving_datetime
                    total_seconds = time_diff.total_seconds()
                    early_hours = int(total_seconds // 3600)
                    early_minutes = int((total_seconds % 3600) // 60)
                    early_seconds = int(total_seconds % 60)
                    rec.early_hrs = f"{early_hours} hours, {early_minutes} minutes, {early_seconds} seconds"
                else:
                    rec.early_hrs = "0 hours, 0 minutes, 0 seconds"

    def confirm_buton(self):
        """Confirm button"""

        def _to_seconds(val):
            """Convert late_hrs string into total seconds"""
            if not val:
                return 0

            if isinstance(val, (int, float)):
                return int(float(val) * 3600)

            if isinstance(val, str):
                val = val.strip().lower()

                match = re.match(r'(\d+)\s*hour[s]?,\s*(\d+)\s*minute[s]?,\s*(\d+)\s*second[s]?', val)
                if match:
                    h, m, s = match.groups()
                    return int(h) * 3600 + int(m) * 60 + int(s)

                match = re.match(r'(\d+)\s*hour[s]?,?\s*(\d+)\s*minute[s]?', val)
                if match:
                    h, m = match.groups()
                    return int(h) * 3600 + int(m) * 60

                match = re.match(r'(\d+)\s*hour[s]?', val)
                if match:
                    return int(match.group(1)) * 3600

                match = re.match(r'(\d+)\s*minute[s]?,?\s*(\d+)\s*second[s]?', val)
                if match:
                    m, s = match.groups()
                    return int(m) * 60 + int(s)

                match = re.match(r'(\d+)\s*minute[s]?', val)
                if match:
                    return int(match.group(1)) * 60

                match = re.match(r'(\d+)\s*second[s]?', val)
                if match:
                    return int(match.group(1))

                if ":" in val:
                    parts = val.split(":")
                    parts = [int(x) for x in parts]
                    while len(parts) < 3:
                        parts.append(0)
                    h, m, s = parts
                    return h * 3600 + m * 60 + s

                try:
                    return int(float(val) * 3600)
                except:
                    return 0

            return 0

        for rec in self:
            rec.write({
                'state': 'request',
                'is_readonly': True,
                'confirm_date': fields.Datetime.now()
            })
            if rec.employee_id.early_late_approve_ids:
                manager_emails = rec.employee_id.early_late_approve_ids.mapped('email')
                manager_emails = ", ".join(manager_emails)
            else:
                raise ValidationError('Please configure early or late approval in employee form')

            if rec.is_app:
                employee_email = rec.employee_id.work_email
                if employee_email:
                    if rec.type == 'early_departure':
                        subject = _('Update Reason For Early Departure')
                        body = _(
                            "<p>Dear {employee_name},</p>"
                            "<p>Your Early Departure request has been recorded. </p>"
                            "<p>Here are the details:</p>"
                            "<strong>Employee Name:</strong> {employee_name}<br>"
                            "<strong>Date:</strong> {date_early}<br>"
                            "<strong>Expected Departure Time:</strong> {time_string}<br>"
                            "<strong>Early By:</strong> {lateness}<br>"
                            "<strong>Reason:</strong> {reason}</p>"
                            "<p>Please review your request in the system.</p>"
                            "<p>Best Regards,<br>Your HR Team</p>"
                        ).format(
                            employee_name=rec.employee_id.name,
                            reason=rec.reason,
                            lateness=rec.early_hrs,
                            date_early=rec.date_early.strftime('%d/%m/%Y'),
                            time_string=rec.time_string
                        )

                    else:
                        subject = _('Update Reason For Late Arrival')

                        start_month = rec.date_late.replace(day=1)
                        end_month = (start_month.replace(month=start_month.month % 12 + 1, day=1) - timedelta(days=1))

                        monthly_records = self.env[rec._name].sudo().search([
                            ('employee_id', '=', rec.employee_id.id),
                            ('date_late', '>=', start_month),
                            ('date_late', '<=', end_month),
                            ('type', '=', 'late_arrival'),
                        ])

                        total_seconds = sum(_to_seconds(r.late_hrs) for r in monthly_records)

                        hours, remainder = divmod(total_seconds, 3600)
                        minutes, seconds = divmod(remainder, 60)
                        cumulative_late_hrs = f"{hours} hours, {minutes} minutes, {seconds} seconds"

                        body = _(
                            "<p>Dear {employee_name},</p>"
                            "<p>Your Late Arrival request has been recorded. </p>"
                            "<p>Here are the details:</p>"
                            "<p><strong>Employee Name:</strong> {employee_name}<br>"
                            "<strong>Date:</strong> {date_late}<br>"
                            "<strong>Arrival Time:</strong> {time_string}<br>"
                            "<strong>Late By:</strong> {lateness}<br>"
                            "<strong>Reason:</strong> {reason}</p>"
                            "<p><strong>Cumulative Late Hours (This Month):</strong> {cumulative}</p>"
                            "<p>Please review your request in the system.</p>"
                            "<p>Best Regards,<br>Your HR Team</p>"
                        ).format(
                            employee_name=rec.employee_id.name,
                            reason=rec.reason,
                            lateness=rec.late_hrs,
                            date_late=rec.date_late.strftime('%d/%m/%Y'),
                            time_string=rec.time_string,
                            cumulative=cumulative_late_hrs
                        )

                    # Generate view link
                    base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                    view_url = "{}/web#id={}&view_type=form&model={}".format(base_url, rec.id, rec._name)

                    html_content = """
                        <div>
                            <a href="{}">
                                <button style='padding:7px;background-color:#71639e;color:white;
                                height:35px;border-radius:10px;'>
                                    VIEW 
                                </button>
                            </a>
                        </div>
                    """.format(view_url)

                    outgoing_mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
                    email_from = outgoing_mail_server.sudo().smtp_user

                    mail_values = {
                        'subject': subject,
                        'body_html': body + "<br/>" + html_content,
                        'email_to': employee_email,
                        'email_from': email_from,
                        'reply_to': rec.employee_id.work_email or email_from,
                    }
                    self.env['mail.mail'].sudo().create(mail_values).send()

            if rec.type == 'early_departure':
                subject = _('Early Departure Approval Request')
                body = _(
                    "<p>Dear Sir/Madam,</p>"
                    "<p>I am requesting your approval for my Early Departure. </p>"
                    "<p>Here are the details:</p>"
                    "<strong>Employee Name:</strong> {employee_name}<br>"
                    "<strong>Date:</strong> {date_early}<br>"
                    "<strong>Expected Departure Time:</strong> {time_string}<br>"
                    "<strong>Early By:</strong> {lateness}<br>"
                    "<strong>Reason:</strong> {reason}</p>"

                    "<p>Thank you for your consideration.</p>"
                    "<p>Best Regards,<br>{employee_name}</p>"
                ).format(employee_name=rec.employee_id.name, reason=rec.reason, lateness=rec.early_hrs,
                         date_early=rec.date_early.strftime('%d/%m/%Y'), time_string=rec.time_string)
            else:
                subject = _('Late Coming Approval Request')

                # compute cumulative late hours for current month
                start_month = rec.date_late.replace(day=1)
                end_month = (start_month.replace(month=start_month.month % 12 + 1, day=1)
                             - timedelta(days=1))

                monthly_records = self.env[rec._name].sudo().search([
                    ('employee_id', '=', rec.employee_id.id),
                    ('date_late', '>=', start_month),
                    ('date_late', '<=', end_month),
                    ('type', '=', 'late_arrival'),
                ])

                total_seconds = sum(_to_seconds(r.late_hrs) for r in monthly_records)

                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)

                cumulative_late_hrs = f"{hours} hours, {minutes} minutes, {seconds} seconds"


                body = _(
                    "<p>Dear Sir/Madam,</p>"
                    "<p>I am requesting your approval for my late arrival. </p>"
                    "<p>Here are the details:</p>"
                    "<p><strong>Employee Name:</strong> {employee_name}<br>"
                    "<strong>Date:</strong> {date_late}<br>"
                    "<strong>Arrival Time:</strong> {time_string}<br>"
                    "<strong>Late By:</strong> {lateness}<br>"
                    "<strong>Reason:</strong> {reason}</p>"
                    "<p><strong>Cumulative Late Hours (This Month):</strong> {cumulative}</p>"
                    "<p>Thank you for your consideration.</p>"
                    "<p>Best Regards,<br>{employee_name}</p>"
                ).format(
                    employee_name=rec.employee_id.name,
                    reason=rec.reason,
                    lateness=rec.late_hrs,
                    date_late=rec.date_late.strftime('%d/%m/%Y'),
                    time_string=rec.time_string,
                    cumulative=cumulative_late_hrs
                )

            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            view_url = "{}/web#id={}&view_type=form&model={}".format(base_url, rec.id, rec._name)
            approve_url = "{}/web/action_first_approval?id={}".format(base_url, rec.id)
            reject_url = "{}/web#action=kg_attendance.action_reject_reason_wizard&active_id={}".format(base_url,
                                                                                                       rec.id)

            html_content = """
                <div>
                    <a href="{}">
                        <button style='padding:7px;background-color:#71639e;color:white;
                        height:35px;border-radius:10px;'>
                            VIEW 
                        </button>
                    </a>
                    <a href="{}">
                        <button style='padding:7px;background-color:#28a745;color:white;
                        height:35px;border-radius:10px;margin-left:10px;'>
                            APPROVE
                        </button>
                    </a> 
                    <a href="{}">
                        <button style='padding:7px;background-color:#AF1740;color:white;
                        height:35px;border-radius:10px;margin-left:10px;'>
                            RETURN
                        </button>
                    </a>
                </div>
            """.format(view_url, approve_url, reject_url)

            outgoing_mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
            email_from = outgoing_mail_server.sudo().smtp_user

            mail_values = {
                'subject': subject,
                'body_html': body + "<br/>" + html_content,
                'email_to': manager_emails,
                'email_from': email_from,
                'reply_to': rec.employee_id.work_email or email_from,
            }
            self.env['mail.mail'].sudo().create(mail_values).send()

    def action_first_approval(self):
        self.sudo().write({
            'state': 'lm_approved'
        })
        return {'success': True}
        # late_approval_ids = self.env['ir.config_parameter'].sudo().get_param('late_sec_approval_ids')
        # group_send_mail = []
        #
        # for config_rec in self.env['res.users'].browse(eval(late_approval_ids)):
        #     if config_rec.email:
        #         group_send_mail.append(config_rec.email)
        # if self.type == 'early_departure':
        #     subject = _('Early Departure Approval Request')
        #     body = _(
        #         "<p>Dear Sir/Madam,</p>"
        #         "<p>I am requesting your approval for my Early Departure. </p>"
        #         "<p>Here are the details:</p>"
        #         "<p><strong>Employee Name:</strong> {employee_name}<br>"
        #         "<strong>Reason:</strong> {reason}<br>"
        #         "<strong>Expected Early Departure:</strong> {lateness}</p>"
        #         "<p>Thank you for your consideration.</p>"
        #         "<p>Best Regards,<br>{employee_name}</p>"
        #     ).format(employee_name=self.employee_id.name, reason=self.reason, lateness=self.early_hrs)
        # else:
        #     subject = _('Late Coming Approval Request')
        #     body = _(
        #         "<p>Dear Sir/Madam,</p>"
        #         "<p>I am requesting your approval for my late arrival. </p>"
        #         "<p>Here are the details:</p>"
        #         "<p><strong>Employee Name:</strong> {employee_name}<br>"
        #         "<strong>Reason:</strong> {reason}<br>"
        #         "<strong>Expected Late Arrival:</strong> {lateness}</p>"
        #         "<p>Thank you for your consideration.</p>"
        #         "<p>Best Regards,<br>{employee_name}</p>"
        #     ).format(employee_name=self.employee_id.name, reason=self.reason, lateness=self.late_hrs)
        # base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        #
        # # approve_url = "{}/project_task_analysis/approve_task?record_id={}".format(base_url, self.id)
        # # discuss_url = "{}/project_task_analysis/discuss_task?record_id={}".format(base_url, self.id)
        # view_url = "{}/web#id={}&view_type=form&model={}".format(base_url, self.id, self._name)
        # approve_url = "{}/web/action_second_approval?id={}".format(base_url, self.id)
        # reject_url = "{}/web/action_reject?id={}".format(base_url, self.id)
        #
        # html_content = """
        #                     <div>
        #                         <a href="{}">
        #                             <button style='padding:7px;background-color:#71639e;color:white;
        #                             height:35px;border-radius:10px;'>
        #                                 VIEW
        #                             </button>
        #                         </a>
        #                          <a href="{}">
        #                                  <button style='padding:7px;background-color:#28a745;color:white;
        #                                  height:35px;border-radius:10px;margin-left:10px;'>
        #                     APPROVE
        #                 </button>
        #             </a>
        #             <a href="{}">
        #                          <button style='padding:7px;background-color:#AF1740;color:white;
        #                          height:35px;border-radius:10px;margin-left:10px;'>
        #             Reject
        #         </button>
        #     </a>
        #                     </div>
        #                 """.format(view_url, approve_url, reject_url)
        # mail_values = {
        #     'subject': subject,
        #     'body_html': body + "<br/>" + html_content,
        #     'email_to': ', '.join(group_send_mail),
        #     'email_from': 'itron@klystronglobal.com',
        # }
        # self.env['mail.mail'].sudo().create(mail_values).send()

    # def action_second_approval(self):
    #     """Second Approval"""
    #     self.write({
    #         'state': 'ceo_approved'
    #     })

    def action_reject(self):
        for rec in self:
            if not rec.reason_for_return:
                raise ValidationError(_('Please provide a reason before proceeding with the return.'))
            rec.state = 'cancel'

    def action_reset_to_draft(self):
        self.write({
            'state': 'draft'
        })

    @api.model
    def send_weekly_late_arrival_report(self):
        today = datetime.today()

        start_of_week = today - timedelta(days=(today.weekday() + 1) % 7)
        end_of_week = start_of_week + timedelta(days=6)

        start_of_week_date = start_of_week.date()
        end_of_week_date = end_of_week.date()

        formatted_start_date = start_of_week_date.strftime('%d/%m/%Y')
        formatted_end_date = today.strftime('%d/%m/%Y')

        late_requests = self.env['early.late.request'].search([
            ('state', '=', 'lm_approved'),
            ('type', '=', 'late_arrival'),
            ('date_late', '>=', start_of_week_date),
            ('date_late', '<=', end_of_week_date),
        ])
        companies = self.env['res.company'].search([])
        report_data = {}

        for company in companies:
            report_data[company.name] = {}
            late_arrivals = late_requests.filtered(lambda x: x.company_name == company)
            for req in late_arrivals:
                employee_name = req.employee_id.name
                lateness_duration = req.late_hrs or "0 hours and 0 minutes"

                if employee_name not in report_data[company.name]:
                    report_data[company.name][employee_name] = {
                        'days': {day: '00:00' for day in
                                 ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']},
                        'total_late_seconds': 0,
                    }

                weekday = req.date_late.weekday()
                if weekday == 6:
                    weekday = 0
                else:
                    weekday += 1
                day_name = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][weekday]

                report_data[company.name][employee_name]['days'][day_name] = req.time_string or '00:00'

                hours, minutes = map(int, [int(s) for s in lateness_duration.split() if s.isdigit()])
                total_seconds = (hours * 3600) + (minutes * 60)
                report_data[company.name][employee_name]['total_late_seconds'] += total_seconds

        filtered_report_data = {company: employees for company, employees in report_data.items() if employees}

        table_content = ""

        for company, requests in filtered_report_data.items():
            table_content += f"<h3><u>{company}</u></h3>"

            table_content += "<table border='1' style='border-collapse: collapse; width: 100%; text-align: left;'>"
            table_content += "<thead><tr><th>Employee Name</th><th>Total Hours</th>"

            for day in ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']:
                table_content += f"<th>{day}</th>"
            table_content += "</tr></thead><tbody>"

            for employee_name, data in requests.items():
                total_seconds = data['total_late_seconds']
                total_hours = total_seconds // 3600
                total_minutes = (total_seconds % 3600) // 60
                total_late_time = f"{total_hours} hours and {total_minutes} minutes"

                table_content += f"<tr><td>{employee_name}</td><td>{total_late_time}</td>"

                for day in ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']:
                    table_content += f"<td>{data['days'].get(day, '00:00')}</td>"

                table_content += "</tr>"

            table_content += "</tbody></table>"

        body = _(
            "<p>Dear Sir,</p>"
            "<p>Please find the Weekly Late arrival report for the period: <strong>{start_date} - {end_date}</strong></p>"
            "{table}"
        ).format(start_date=formatted_start_date, end_date=formatted_end_date, table=table_content)

        outgoing_mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
        email_from = outgoing_mail_server.sudo().smtp_user if outgoing_mail_server else 'itron@klystronglobal.comm'
        group_id = self.env.ref('kg_attendance.all_approval_access')
        admin_emails = group_id.users.mapped('email')
        admin_email = ", ".join(admin_emails) if admin_emails else None
        if not admin_email:
            raise UserError("No approvers found in the 'All Approver' group.")

        mail_values = {
            'subject': "Weekly Late Arrival Report",
            'body_html': body,
            'email_to': admin_email,
            'email_from': email_from,
        }
        self.env['mail.mail'].sudo().create(mail_values).send()

    @api.model
    def auto_approve_late_requests(self):
        requests = self.search([
            ('state', '=', 'request'),
            ('type', '=', 'late_arrival')
        ])

        group_id = self.env.ref('kg_attendance.all_approval_access')  # Reference the group
        admin_emails = group_id.users.mapped('email')  # Fetch emails of all users in the group
        admin_email = ", ".join(admin_emails) if admin_emails else None
        if not admin_email:
            raise UserError("No approvers found in the 'All Approver' group.")

        for request in requests:
            # Ensure tz is valid before using it
            employee_tz = pytz.timezone(request.employee_id.tz) if request.employee_id.tz else pytz.utc

            # Localize the current UTC time to the employee's timezone
            now_utc = datetime.now(pytz.utc)
            localized_now = now_utc.astimezone(employee_tz)

            two_hours_ago = localized_now - timedelta(hours=3)

            # Ensure confirm_date is a valid datetime object before localizing it
            if request.confirm_date:
                confirm_date_localized = pytz.utc.localize(request.confirm_date).astimezone(employee_tz)

                if confirm_date_localized <= two_hours_ago:
                    request.write({'state': 'lm_approved'})
                    recipients = []
                    if request.employee_id.early_late_approve_ids:
                        recipients = request.employee_id.early_late_approve_ids.mapped('email')

                    if admin_email:
                        recipients.append(admin_email)

                    subject = "Late Request Automatically Approved"
                    button_style = (
                        "display: inline-block; padding: 10px 10px; font-size: 16px; "
                        "color: white; background-color: #007bff; text-decoration: none; "
                        "border-radius: 5px;"
                    )
                    body = _(
                        "<p>Dear Sir/Ma'am,</p>"
                        "<p>The late request for <strong>{employee_name}</strong> has been automatically approved.</p>"
                        "<p>Please review the details by clicking the button below:</p>"
                        "<p><a href='{url}' style='{style}'>View</a></p>"
                        "<p>Thank you.</p>"
                    ).format(
                        employee_name=request.employee_id.name,
                        url=f"{self.env['ir.config_parameter'].sudo().get_param('web.base.url')}/web#id={request.id}&view_type=form&model=early.late.request",
                        style=button_style,
                    )
                    outgoing_mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
                    email_from = outgoing_mail_server.sudo().smtp_user if outgoing_mail_server else 'itron@klystronglobal.com'

                    mail_values = {
                        'subject': subject,
                        'body_html': body,
                        'email_to': ','.join(recipients),
                        'email_from': email_from,
                    }
                    self.env['mail.mail'].sudo().create(mail_values).send()
            else:
                print(f"Invalid confirm_date for request {request.id}, skipping.")

    @api.model
    def monthly_late_arrival_report(self):
        today = datetime.today()
        start_of_month = today.replace(day=1)

        next_month = start_of_month.replace(day=28) + timedelta(days=4)

        end_of_month = next_month - timedelta(days=next_month.day)

        start_of_month_date = start_of_month.date()
        end_of_month_date = end_of_month.date()

        formatted_start_date = start_of_month_date.strftime('%d/%m/%Y')

        formatted_end_date = end_of_month_date.strftime('%d/%m/%Y')

        #
        # # Get all late arrival requests within the month
        late_requests = self.env['early.late.request'].search([
            # ('state', '=', 'lm_approved'),
            ('type', '=', 'late_arrival'),
            ('date_late', '>=', start_of_month_date),
            ('date_late', '<=', end_of_month_date),
        ], order='date_late ASC')
        #
        print(late_requests, 'late_requests')
        companies = self.env['res.company'].search([])
        print(companies, 'companies')

        report_data = {}
        print(report_data, 'report_data')

        for company in companies:
            report_data[company.name] = {}
            late_arrivals = late_requests.filtered(lambda x: x.company_name == company)

            # Get the start of the current month (first day of the month)
            start_of_month = datetime.now().replace(day=1)

            # Calculate the start and end of weeks 1 to 5 in the current month
            for week_num in range(1, 6):
                week_start = start_of_month + timedelta(weeks=week_num - 1) - timedelta(
                    days=start_of_month.weekday())  # Start of the week
                week_end = week_start + timedelta(days=6)  # End of the week (7 days from week_start)

                # Print the week start and end for debugging
                print(f"Week {week_num} Start: {week_start.date()}, Week {week_num} End: {week_end.date()}")

                # Process late arrivals for the current week (week_start to week_end)
                for req in late_arrivals:
                    employee_name = req.employee_id.name
                    lateness_duration = req.late_hrs or "0 hours and 0 minutes"

                    # Initialize the employee data structure if not already present
                    if employee_name not in report_data[company.name]:
                        report_data[company.name][employee_name] = {
                            'weeks': {f"Week {i}": {'days': {day: '00:00' for day in
                                                             ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday',
                                                              'Friday', 'Saturday']},
                                                    'total_late_seconds': 0} for i in range(1, 6)},
                            'total_late_seconds': 0,
                        }

                    # Check if req.date_late is within the current week (week_start to week_end)
                    if week_start.date() <= req.date_late <= week_end.date():
                        # Determine the weekday (0=Monday, 6=Sunday)
                        weekday = req.date_late.weekday()
                        # day_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][
                        #     weekday]
                        day_name = req.date_late.strftime('%Y-%m-%d')
                        # Get the specific week data for the current week
                        week_data = report_data[company.name][employee_name]['weeks'][f"Week {week_num}"]

                        # Update lateness information for the specific day
                        week_data['days'][day_name] = req.time_string or '00:00'

                        # Convert lateness duration to total seconds
                        lateness_parts = [int(part) for part in lateness_duration.split() if part.isdigit()]
                        hours = lateness_parts[0] if len(lateness_parts) > 0 else 0
                        minutes = lateness_parts[1] if len(lateness_parts) > 1 else 0
                        total_seconds = (hours * 3600) + (minutes * 60)

                        # Accumulate total lateness for the week and employee
                        week_data['total_late_seconds'] += total_seconds
                        report_data[company.name][employee_name]['total_late_seconds'] += total_seconds

        filtered_report_data = {company: employees for company, employees in report_data.items() if employees}

        # Build the table content for email
        table_content = ""

        for company, requests in filtered_report_data.items():
            table_content += f"<h3><u>{company}</u></h3>"

            table_content += "<table border='1' style='border-collapse: collapse; width: 100%; text-align: left;'>"
            table_content += "<thead><tr><th>Employee Name</th><th>Total Hours</th>"

            for week in ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5']:
                table_content += f"<th>{week}</th>"
            table_content += "</tr></thead><tbody>"

            for employee_name, data in requests.items():
                total_seconds = data['total_late_seconds']
                total_hours = total_seconds // 3600
                total_minutes = (total_seconds % 3600) // 60
                total_late_time = f"{total_hours:02}:{total_minutes:02} hours"
                table_content += f"<tr><td>{employee_name}</td><td>{total_late_time}</td>"

                for week in ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5']:
                    week_data = data['weeks'][week]
                    total_week_seconds = week_data['total_late_seconds']
                    week_hours = total_week_seconds // 3600
                    week_minutes = (total_week_seconds % 3600) // 60
                    week_late_time = f"{week_hours} hours and {week_minutes} minutes"

                    day_details = ""
                    for day, time in week_data['days'].items():
                        if time != '00:00':
                            # Parse the full date and extract the day of the month
                            day_date = datetime.strptime(day,
                                                         "%Y-%m-%d").date().strftime(
                                '%d-%m-%Y')  # 'day' now contains full date in 'YYYY-MM-DD' format
                            # day_of_month = day_date.day  # Get the day as an integer (e.g., 23)

                            # Format the day and time
                            day_time = f"{time} ({day_date})"
                            day_details += f"<tr><td>{day_time}</td></tr>"

                    table_content += f"<td><table>{day_details}</table></td>"

                table_content += "</tr>"

            table_content += "</tbody></table>"

        body = _(
            "<p>Dear Sir,</p>"
            "<p>Please find the Monthly Late arrival report for the period: <strong>{start_date} - {end_date}</strong></p>"
            "{table}"
        ).format(start_date=formatted_start_date, end_date=formatted_end_date, table=table_content)

        outgoing_mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
        email_from = outgoing_mail_server.sudo().smtp_user if outgoing_mail_server else 'itron@klystronglobal.comm'
        group_id = self.env.ref('kg_attendance.all_approval_access')
        admin_emails = group_id.users.mapped('email')
        admin_email = ", ".join(admin_emails) if admin_emails else None
        if not admin_email:
            raise UserError("No approvers found in the 'All Approver' group.")

        mail_values = {
            'subject': "Monthly Late Arrival Report",
            'body_html': body,
            'email_to': admin_email,
            'email_from': email_from,
        }
        self.env['mail.mail'].sudo().create(mail_values).send()


class HREmployee(models.Model):
    _inherit = 'hr.employee'

    is_check_employee = fields.Boolean(string="Restrict Late Arrival", default=False)


class HREmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    is_check_employee = fields.Boolean(string="Restrict Late Arrival", default=False)
