import base64
import datetime
import functools
import json
import logging
from datetime import date
from datetime import datetime,timedelta ,time

import pytz

from odoo import http, _, fields
from odoo.addons.kg_base_api.common import (valid_response, invalid_response, ROUTE_BASE, get_user)
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.exceptions import UserError
from odoo.http import request

_logger = logging.getLogger(__name__)


def json_exception_handler(func):
    """Calls the given function by by-passing the error and convert it to a
        json/http response type(dedicated to only json type requests.)"""

    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except (AccessError, MissingError) as e:
            return invalid_response('Access/Missing Error', e, 503, False)
        except (UserWarning, UserError) as e:
            return invalid_response('User Error/Warning', e, 503, False)
        # except Exception as e:
        #     if 'is not present in table' in str(e):
        #         return invalid_response('Invalid Argument',
        #                                 'One of the passed values(database ID) does not exist or has been deleted in the server.', 503,
        #                                 False)
        #     return invalid_response('Unknown Exception', e, 503, False)

    return wrap


def validate_json_token(func):
    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        """."""
        access_token = request.httprequest.headers.get("session_token")
        # data = json.loads(request.httprequest.data)
        # access_token = data.get("session_token")
        if not access_token:
            return invalid_response("Token Not Found",
                                    "missing access token(session_token) in request header", 401, is_http=False)
        access_token_payload = (
            request.env["api.access_token"].sudo().search([("token", "=", access_token)], order="id DESC", limit=1)
        )

        if access_token_payload.find_one_or_create_token(user_id=access_token_payload.user_id.id) != access_token:
            return invalid_response("Token Expired", "token seems to have expired or invalid", 401, is_http=True)

        request.session.uid = access_token_payload.user_id.id
        # request.uid = access_token_payload.user_id.id
        return func(self, *args, **kwargs)

    return wrap


class klystronPost(http.Controller):
    """
    This class includes all end-points need to be interacted with external APIs.
    """

    def conv_time_float(self, value):
        vals = value.split(':')
        t, hours = divmod(float(vals[0]), 24)
        t, minutes = divmod(float(vals[1]), 60)
        minutes = minutes / 60.0
        return hours + minutes

    @validate_json_token
    @json_exception_handler
    @http.route(ROUTE_BASE + 'create_timesheet', type="json", auth="public", methods=["POST"], csrf=False)
    def create_timesheet(self, **payload):
        data = json.loads(request.httprequest.data)
        user = data.get('user_id', False) or payload.get('user_id', False)
        user_id = get_user(user)
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', user_id.id)])
        if data.get('timesheet_id'):
            timesheet = request.env['account.analytic.line'].sudo().browse(data.get('timesheet_id'))
            time = data.get('total_time')
            a, b, c = time.split(':')
            d = a + ':' + b
            z = self.conv_time_float(d)
            sheet_date = data.get('picked_date')
            sheet_date_obj = datetime.strptime(sheet_date, "%d-%m-%Y") if data.get('picked_date') else ''
            start = data.get('start_date_time')
            datetime_object = datetime.strptime(start, "%d-%m-%Y %H:%M:%S") if start else ''
            end = data.get('end_date_time')
            datetime_object_end = datetime.strptime(end, "%d-%m-%Y %H:%M:%S") if end else ''
            values = timesheet.update({
                'date': sheet_date_obj,
                'employee_id': employee.id or False,
                'name': data.get('task_description'),
                'project_id': data.get('project_id'),
                'task_id': data.get('task_id'),
                'date_start': datetime_object,
                'date_end': datetime_object_end,
                'unit_amount': float(z),
            })
            timesheets = timesheet.update({
                'timesheet_ids': values
            })
            return valid_response(timesheets, message='Project Task Timesheet Updated Successfully',
                                  is_http=False)
        else:
            time = data.get('total_time')
            a, b, c = time.split(':')
            d = a + ':' + b
            z = self.conv_time_float(d)
            employee = request.env['hr.employee'].sudo().search([('user_id', '=', user_id.id)])
            task = data.get('task_name')
            task_id = request.env['project.task'].sudo().search([('id', '=', data.get('task_id'))])
            start = data.get('start_date_time')
            end = data.get('end_date_time')
            create_date = data.get('create_date')

            datetime_object = datetime.strptime(start, "%d-%m-%Y %H:%M:%S")
            datetime_object_end = datetime.strptime(end, "%d-%m-%Y %H:%M:%S")
            date_create_date = datetime.strptime(create_date, "%d-%m-%Y")

            values = []
            if task_id:
                values.append((0, 0, {
                    'date': date_create_date,
                    'employee_id': employee.id,
                    'name': data.get('task_description'),
                    'unit_amount': float(z),
                    'date_start': datetime_object,
                    'date_end': datetime_object_end

                })),
            timesheets = task_id.update({
                'timesheet_ids': values
            })
            return valid_response(timesheets, message='Project Task timesheet created successfully',
                                  is_http=False)

    def _create_attachment(self, file, res_id):
        if not file:
            return False
        Attachment = request.env['ir.attachment'].sudo()
        attachment_id = Attachment.create({
            'name': request.env.user.name,
            'type': 'binary',
            'datas': file.encode(),
            'res_model': 'res.partner',
            'res_id': res_id
        })
        return attachment_id.datas

    @validate_json_token
    @json_exception_handler
    @http.route(ROUTE_BASE + 'create_timeoff', type="json", auth="public", methods=["POST"], csrf=False)
    def create_timeoff(self, **payload):
        data = json.loads(request.httprequest.data)
        user = data.get('user_id', False) or payload.get('user_id', False)
        user_id = get_user(user)
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', user_id.id)])
        date_start_str = str(data.get('start_date_time'))
        date_start_object = datetime.strptime(date_start_str, '%d-%m-%Y').date()
        date_end_str = str(data.get('end_date_time'))
        date_end_object = datetime.strptime(date_end_str, '%d-%m-%Y').date()
        values = []
        if employee:
            if data.get('requires_attachment'):
                attachment = request.env['ir.attachment'].sudo()
                attachment_id = attachment.create({
                    'name': data.get('attachment_name'),
                    'type': 'binary',
                    'datas': data.get('attachment').encode(),
                    'mimetype': data.get('attachment_type')

                })
                values.append({
                    'employee_id': employee.id,
                    'user_id': int(user_id.id),
                    'holiday_status_id': int(data.get('leave_type')),
                    'request_date_from': date_start_object,
                    'date_from': date_start_object,
                    'request_date_to': date_end_object,
                    'date_to': date_end_object,
                    'timezone': str(data.get('time_zone')),
                    'utc_time': str(data.get('utc_time')),
                    'name': str(data.get('leave_description')),
                    # 'employee_company_id': request.env.company.id or 0,
                    'mode_company_id': request.env.company.id or 0,
                    'attach_ids': [(6, 0, [attachment_id.id])]
                })
            else:
                values.append({
                    'employee_id': employee.id,
                    'user_id': int(user_id.id),
                    'holiday_status_id': int(data.get('leave_type')),
                    'request_date_from': date_start_object,
                    'date_from': date_start_object,
                    'request_date_to': date_end_object,
                    'date_to': date_end_object,
                    'timezone': str(data.get('time_zone')),
                    'utc_time': str(data.get('utc_time')),
                    'name': str(data.get('leave_description')),
                    # 'employee_company_id': request.env.company.id or 0,
                    'mode_company_id': request.env.company.id or 0,
                })
        leave = request.env['hr.leave'].sudo().create(values)
        return valid_response(leave.id, message='Leave request created successfully',
                              is_http=False)

    @validate_json_token
    @json_exception_handler
    @http.route(ROUTE_BASE + 'create_expenses', type="json", auth="public", methods=["POST"], csrf=False)
    def create_expenses(self, **payload):
        data = json.loads(request.httprequest.data)
        user = data.get('user_id', False) or payload.get('user_id', False)
        user_id = get_user(user)
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', user_id.id)])
        date_str = str(data.get('expense_date'))
        date_object = datetime.strptime(date_str, '%d-%m-%Y').date()
        values = []

        if employee:
            category = []

            for i in data.get('expense_line_ids'):
                if i['attach']:
                    attachment = request.env['ir.attachment'].sudo()
                    attachment_id = attachment.create({
                        'name': i['attachment_name'],
                        'type': 'binary',
                        'datas': base64.b64encode(i['attach'].encode('utf-8')),
                        'mimetype': i['attachment_type']
                    })
                    # for j in attachment_id:
                    category.append(
                        (0, 0, {"category_id": i["category_id"], "cost": i["cost"],
                                "attachment_ids": [(6, 0, [attachment_id.id])]}))
                else:
                    category.append(
                        (0, 0, {"category_id": i["category_id"], "cost": i["cost"],
                                "attachment_ids": False}))
            values.append({
                'name': str(data.get('name')),
                'employee_id': employee.id,
                'expense_date': date_object,
                'currency_id': data.get('currency_id'),
                'expense_line_ids': category,

                'company_id': request.env.company.id or 0,
            })
        expense = request.env['kg.expense'].sudo().create(values)
        return valid_response(values, message='Expense created successfully',
                              is_http=False)

    @validate_json_token
    @json_exception_handler
    @http.route(ROUTE_BASE + 'create_helpdesk', type="json", auth="public", methods=["POST"], csrf=False)
    def create_helpdesk(self, **payload):
        data = json.loads(request.httprequest.data)
        user = data.get('user_id', False) or payload.get('user_id', False)
        values = [{
            'name': str(data.get('title')) or '',
            'partner_id': request.env.user.partner_id.id or 0,
            'partner_name': request.env.user.partner_id.name or '',
            "category_id": data.get('category_id') or 0,
            'description': str(data.get('description')) or '',
            'company_id': request.env.company.id or 0,
            # 'currency_id': request.env.ref('base.main_company').currency_id.id,
            # 'payment_mode': 'own_account'
        }]
        helpdesk = request.env['helpdesk.ticket'].sudo().create(values)
        return valid_response(values, message='Helpdesk created successfully',
                              is_http=False)

    @validate_json_token
    @json_exception_handler
    @http.route(ROUTE_BASE + "attendance", type="json", auth="public", methods=["POST"], csrf=False)
    def record_attendance(self, **payload):
        """
        Register a check-in or check-out event based on payload action.
        """
        data = json.loads(request.httprequest.data)
        employee_id = data.get('employee_id', False) or payload.get('employee_id', False)
        action = data.get('action', False) or payload.get('action', False)
        company = request.env['res.company'].search([]).filtered(lambda x: x.country_code == 'IN')
        print(f"{company.name} - {company.country_id.name} - {company.country_id.code}", 'dddddddddddd')

        if not employee_id or action not in ["checkin", "checkout"]:
            return invalid_response(
                "invalid_payload",
                "employee_id and action (checkin/checkout) are required",
                400
            )

        employee = request.env["hr.employee"].sudo().search([("id", "=", employee_id)], limit=1)
        if not employee:
            return invalid_response("invalid_employee", f"No employee found with ID {employee_id}", 404)
        if action == "checkin":
            today = fields.Date.today()
            now = fields.Datetime.now()

            last_attendance = request.env["hr.attendance"].sudo().search([
                ("employee_id", "=", employee.id),
                ("check_in", "<", today)
            ], order="check_in desc", limit=1)

            if last_attendance and not last_attendance.check_out:
                return invalid_response(
                    "missing_checkout",
                    f"Employee {employee.name} did not mark checkout on {last_attendance.check_in.strftime('%Y-%m-%d')}",
                    400
                )

            already_checked_today = request.env["hr.attendance"].sudo().search([
                ("employee_id", "=", employee.id),
                ("check_in", ">=", today),
                ("check_in", "<", today + timedelta(days=1))
            ], limit=1)

            if already_checked_today:
                return invalid_response(
                    "already_checked_today",
                    f"Employee {employee.name} has already checked in on {today}",
                    400
                )

            record = request.env["hr.attendance"].sudo().create({
                "employee_id": employee.id,
                "check_in": fields.Datetime.now(),
                'in_mode': 'app'
            })

            employee_tz = pytz.timezone(employee.tz or 'UTC')
            now_local = now.astimezone(employee_tz)
            today_local = now_local.date()
            time_local = now_local.time()

            weekday = today_local.weekday()

            calendar = employee.resource_calendar_id
            if not calendar:
                print("No work schedule for employee — skipping late check")
            else:
                attendances = calendar.attendance_ids.filtered(
                    lambda a: int(a.dayofweek) == weekday
                )

                if not attendances:
                    print("No work schedule for this day — skipping late check")
                else:
                    # Check for half-day morning leave
                    # Check for half-day morning leave
                    morning_leave = request.env['hr.leave'].sudo().search([
                        ('employee_id', '=', employee.id),
                        ('state', '!=', 'refuse'),  # approved
                        ('request_date_from', '<=', today),
                        ('request_date_to', '>=', today),
                        ('request_unit_half', '=', True),
                        ('request_date_from_period', '=', 'am')
                    ], limit=1)

                    if morning_leave:
                        print('baii')
                        # Fetch the attendance slot for today's afternoon
                        afternoon_attendance = employee.resource_calendar_id.attendance_ids.filtered(
                            lambda a: int(a.dayofweek) == weekday and a.day_period == 'afternoon'
                        )
                        print(afternoon_attendance,'pppppppppp')
                        if afternoon_attendance:
                            earliest_attendance = min(afternoon_attendance, key=lambda a: a.hour_from)
                        else:
                            earliest_attendance = False
                        print('eR',earliest_attendance.name)
                    else:
                        print('hai')
                        # No morning leave → take earliest slot for the day
                        day_attendance = employee.resource_calendar_id.attendance_ids.filtered(
                            lambda a: int(a.dayofweek) == weekday
                        )
                        if day_attendance:
                            earliest_attendance = min(day_attendance, key=lambda a: a.hour_from)
                        else:
                            earliest_attendance = False

                    # Late arrival check
                    if earliest_attendance:
                        start_hour = int(earliest_attendance.hour_from)
                        start_minute = int((earliest_attendance.hour_from % 1) * 60)
                        work_start_time = time(start_hour, start_minute)
                        print(work_start_time,'pppppppp')

                        if time_local > work_start_time:
                            late_arrival = request.env['early.late.request'].sudo().create({
                                'employee_id': employee.id,
                                'type': 'late_arrival',
                                'date_late': today,
                                'reason': 'Late Entry',
                                'company_name': employee.company_id.id or False,
                                'hours': str(now_local.hour),
                                'minutes': str(now_local.minute),
                                'seconds': str(now_local.second),
                                'is_app': True,
                            })
                            late_arrival.sudo().confirm_buton()
                        else:
                            print("On time or early — no late request created")

            response_data = {
                "employee_id": employee.id,
                "checkin_time": str(record.check_in),
                'in_mode': 'app',

            }
        else:
            today = fields.Date.today()
            last_attendance = request.env["hr.attendance"].sudo().search([
                ("employee_id", "=", employee.id),
                ("check_in", ">=", today),
                ("check_in", "<", today + timedelta(days=1)),
                ("check_out", "=", False)
            ], order="check_in DESC", limit=1)

            if not last_attendance:
                return invalid_response(
                    "no_open_attendance",
                    f"No active check-in found for {employee.name} today to check out",
                    404
                )

            if last_attendance.check_out:
                return invalid_response(
                    "already_checked_out",
                    f"Employee {employee.name} has already checked out today",
                    400
                )

            last_attendance.check_out = fields.Datetime.now()
            last_attendance.out_mode = 'app'

            response_data = {
                "employee_id": employee.id,
                "checkin_time": str(last_attendance.check_in),
                "checkout_time": str(last_attendance.check_out),
                'in_mode': 'app',
                'out_mode': 'app'

            }

        return valid_response(response_data, message=f"{action.capitalize()} recorded successfully", is_http=True)

