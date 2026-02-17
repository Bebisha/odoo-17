import functools
import logging
import json
import time
from datetime import timedelta, date
from odoo.tools.float_utils import float_round

import datetime
from datetime import datetime
from odoo import http, _, fields
from odoo.addons.kg_base_api.common import (valid_response, invalid_response, ROUTE_BASE, get_user,
                                            _convert_image_to_base64)
from odoo.exceptions import UserError, MissingError, AccessError
from odoo.http import request

_logger = logging.getLogger(__name__)


def http_exception_handler(func):
    """Calls the given function by by-passing the error and convert it to a
        json/http response type(dedicated to only http type requests.)"""

    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        """."""
        try:
            return func(self, *args, **kwargs)
        except (AccessError, MissingError) as e:
            return invalid_response('Access/Missing Error', e, 503, True)
        except (UserWarning, UserError) as e:
            return invalid_response('User Error/Warning', e, 503, True)
        except Exception as e:
            if 'is not present in table' in str(e):
                return invalid_response('Invalid Argument',
                                        'One of the passed values(database ID) is not present in the server.', 503,
                                        True)
            return invalid_response('Exception', e, 503, True)

    return wrap


def validate_http_token(func):
    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        """."""
        access_token = request.httprequest.headers.get("session_token")
        session_key = request.httprequest.cookies.get('session_id')
        if not access_token:
            return invalid_response("Token Not Found", "Missing access token loginnnn(session_token) in request header",
                                    401, True)
        access_token_payload = (
            request.env["api.access_token"].sudo().search([("token", "=", access_token)], order="id DESC", limit=1))

        if access_token_payload.find_one_or_create_token(user_id=access_token_payload.user_id.id) != access_token:
            return invalid_response("Token Expired", "Token seems to have expired or invalid", 401, True)

        request.session.uid = access_token_payload.user_id.id
        # request.uid = access_token_payload.user_id.id
        return func(self, *args, **kwargs)

    return wrap


class KlystronApiGet(http.Controller):
    """
    This class includes all end-points need to be interacted with external APIs.
    """

    @validate_http_token
    @http_exception_handler
    @http.route(ROUTE_BASE + 'get_project_task', type="http", auth="public", methods=["GET"], csrf=False)
    def get_project_task(self, **payload):
        """returns product data based on the given criteria."""
        user_id = get_user(payload.get('user_id', False))
        task = request.env['project.task'].sudo().search([('user_ids', 'in', user_id.id)])
        todo_datas = []
        in_progress_datas = []
        closed_datas = []
        task_id = request.env['project.task'].sudo().search(
            [('user_ids', 'in', user_id.id), ('stage_id.is_open', '=', True)])
        for to in task_id:
            if to:
                todo_datas.append({
                    'task_id': to.id or 0,
                    'task_name': to.name or '',
                    'task_description': to.description or '',
                    'date_deadline': to.date_deadline.strftime("%d-%m-%Y") if to.date_deadline else '',
                    'task_start_date': to.date_assign.strftime("%d-%m-%Y %H:%M:%S") if to.date_assign else '',
                    'task_end_date': to.date_end.strftime("%d-%m-%Y %H:%M:%S") if to.date_end else '',
                    'total_time': to.planned_hours or 0.00,
                    'hours_spend': to.effective_hours or 0.00,
                    'status': to.stage_id.name or '',
                    'project_name': to.project_id.name or '',
                })

        in_task = request.env['project.task'].sudo().search(
            [('user_ids', 'in', user_id.id), ('stage_id.is_closed', '=', False), ('stage_id.is_open', '=', False)])
        for ta in in_task:
            if ta:
                in_progress_datas.append({
                    'task_id': ta.id or 0,
                    'task_name': ta.name or '',
                    'task_description': ta.description or '',
                    'date_deadline': ta.date_deadline.strftime("%d-%m-%Y") if ta.date_deadline else '',
                    'task_start_date': ta.date_assign.strftime("%d-%m-%Y %H:%M:%S") if ta.date_assign else '',
                    'task_end_date': ta.date_end.strftime("%d-%m-%Y %H:%M:%S") if ta.date_end else '',
                    'total_time': ta.planned_hours or 0.00,
                    'hours_spend': ta.effective_hours or 0.00,
                    'status': ta.stage_id.name or '',
                    'project_name': ta.project_id.name or '',
                })
        closed_task = request.env['project.task'].sudo().search(
            [('user_ids', 'in', user_id.id), ('stage_id.is_closed', '=', True)])
        for k in closed_task:
            closed_datas.append({
                'task_id': k.id or 0,
                'task_name': k.name or '',
                'task_description': k.description or '',
                'date_deadline': k.date_deadline.strftime("%d-%m-%Y") if k.date_deadline else '',
                'task_start_date': k.date_assign.strftime("%d-%m-%Y %H:%M:%S") if k.date_assign else '',
                'task_end_date': k.date_end.strftime("%d-%m-%Y %H:%M:%S") if k.date_end else '',
                'total_time': k.planned_hours or 0.00,
                'hours_spend': k.effective_hours or 0.00,
                'status': k.stage_id.name or '',
                'project_name': k.project_id.name or '',
            })
        values = {
            'user_id': user_id.id,
            'Todo': todo_datas,
            'In Progress': in_progress_datas,
            'Closed': closed_datas
        }
        return valid_response(values, message='Get Project task data has been fetched successfully', is_http=True)

    @validate_http_token
    @http_exception_handler
    @http.route(ROUTE_BASE + 'get_all_projects', type="http", auth="public", methods=["GET"], csrf=False)
    def get_all_projects(self, **payload):
        user = get_user(payload.get('user_id'))
        project = request.env['project.project'].sudo().search([('project_team_user_ids', '=', user.id)])
        vals = []
        if project:
            for pro in project:
                vals.append({
                    'project_name': pro.name or '',
                    'project_id': pro.id or 0,
                })
        values = {
            'user_id': user.id,
            'daily': vals,
        }
        # return json.dumps(values)
        return valid_response(values, message='All Project data has been fetched successfully', is_http=True)

    @validate_http_token
    @http_exception_handler
    @http.route(ROUTE_BASE + 'get_all_tasks', type="http", auth="public", methods=["GET"], csrf=False)
    def get_all_tasks(self, **payload):
        user = get_user(payload.get('user_id'))
        proj = payload.get('project_id')
        project = request.env['project.task'].sudo().search(
            [('user_ids', 'in', user.id), ('stage_id.is_closed', '=', False)])
        vals = []
        if project:
            for pro in project:
                vals.append({
                    'task_name': pro.name or '',
                    'task_id': pro.id or 0,
                    'project_id': pro.project_id.id or 0,
                    'project_name': pro.project_id.name or '',
                })
        values = {
            'user_id': user.id,
            'Tasks': vals,
        }
        # return json.dumps(values)
        return valid_response(values, message='All Task data has been fetched successfully', is_http=True)

    @validate_http_token
    @http_exception_handler
    @http.route(ROUTE_BASE + 'get_timesheet_daily', type="http", auth="public", methods=["GET"], csrf=False)
    def get_timesheet_daily(self, **payload):
        user = get_user(payload.get('user_id'))
        today = date.today()
        employee_id = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)])
        tasks = request.env['account.analytic.line'].sudo().search(
            [('employee_id', '=', employee_id.id), ('date', '=', today)])
        datas = []
        for i in tasks:
            if i.date == today:
                datas.append({
                    'task_id': i.task_id.id or 0,
                    'task_name': i.task_id.name or '',
                    'task_description': i.name or '',
                    'timesheet_id': i.id or 0,
                    'task_deadline': i.task_id.date_deadline.strftime("%d/%m/%Y") or '',
                    'start_date': i.date_start.strptime("%d/%m/%Y %H:%M:%S") or '',
                    'end_date': i.date_end.strptime("%d/%m/%Y %H:%M:%S") or '',
                    'planned_hours': i.task_id.planned_hours or 0.00,
                    'hours_spend': i.task_id.effective_hours or 0.00,
                    'status': i.task_id.stage_id.name or '',
                    'status_id': i.task_id.stage_id.id or 0,
                    'project_name': i.project_id.name or '',
                    'project_id': i.project_id.id or 0
                })

        values = {
            'user_id': user.id,
            'daily': datas,
        }
        return valid_response(values, message='Project Task data has been fetched successfully', is_http=True)

    def getDateRangeFromWeek(self, p_year, p_week):
        firstdayofweek = datetime.strptime(f'{p_year}-W{int(p_week) - 1}-1', "%Y-W%W-%w").date()
        lastdayofweek = firstdayofweek + timedelta(days=6.9)
        return firstdayofweek, lastdayofweek

    def get_first_date_of_current_month(self, year, month):
        """Return the first date of the month.

        Args:
            year (int): Year
            month (int): Month

        Returns:
            date (datetime): First date of the current month
        """
        first_date = datetime(year, month, 1)
        return first_date.strftime("%Y-%m-%d")

    def get_last_date_of_month(self, year, month):
        """Return the last date of the month.

        Args:
            year (int): Year, i.e. 2022
            month (int): Month, i.e. 1 for January

        Returns:
            date (datetime): Last date of the current month
        """

        if month == 12:
            last_date = datetime(year, month, 31)
        else:
            last_date = datetime(year, month + 1, 1) + timedelta(days=-1)

        return last_date.strftime("%Y-%m-%d")

    @validate_http_token
    @http_exception_handler
    @http.route(ROUTE_BASE + 'get_timesheet_weekly', type="http", auth="public", methods=["GET"], csrf=False)
    def get_timesheet_weekly(self, **payload):
        user = get_user(payload.get('user_id'))
        my_date = date.today()
        year, week_num, day_of_week = my_date.isocalendar()
        firstdate, lastdate = self.getDateRangeFromWeek(year, week_num)
        tasks = request.env['project.task'].sudo().search(
            [('date_assign', '>', firstdate), ('date_end', '<', lastdate), ('user_ids', 'in', user.id)])
        weekly = []
        for i in tasks:
            weekly.append({
                'task_id': i.id or 0,
                'task_name': i.name or '',
                'task_description': i.description or '',
                'task_deadline': i.date_deadline.strftime("%d/%m/%Y") if i.date_deadline else '',
                'task_start_date': i.date_assign.strftime("%d/%m/%Y %H:%M:%S") if i.date_assign else '',
                'task_end_date': i.date_end.strftime("%d/%m/%Y %H:%M:%S") if i.date_end else '',
                'total_time': i.effective_hours or 0.00,
                'project_name': i.project_id.name or '',
                'project_id': i.project_id.id or 0,
                'status': i.stage_id.name or '',
            })
        current_month = my_date.strftime("%m")
        month_start = self.get_first_date_of_current_month(year, int(current_month))
        month_end = self.get_last_date_of_month(year, int(current_month))
        monthly_tasks = request.env['project.task'].sudo().search(
            [('date_assign', '>', month_start), ('date_end', '<', month_end), ('user_ids', 'in', user.id)])
        month = []
        for k in monthly_tasks.timesheet_ids:
            month.append({
                'task_id': k.task_id.id or 0,
                'task_name': k.task_id.name or '',
                'task_description': k.name or '',
                'task_deadline': k.date_deadline.strftime("%d/%m/%Y") if k.date_deadline else '',
                'task_start_date': k.task_id.date_assign.strftime("%d/%m/%Y %H:%M:%S") if k.task_id.date_assign else '',
                'task_end_date': k.task_id.date_end.strftime("%d/%m/%Y %H:%M:%S") if k.task_id.date_end else '',
                'total_time': k.task_id.effective_hours or 0.00,
                'project_name': k.project_id.name or '',
                'project_id': k.project_id.id or 0,
                'status': k.task_id.stage_id.name or '',
            })
        current_quarter = round((my_date.month - 1) / 3 + 1)
        first_date = datetime(my_date.year, 3 * current_quarter - 2, 1)
        last_date = datetime(my_date.year, 3 * current_quarter, 31) \
                    + timedelta(days=-1)
        qtrly_tasks = request.env['project.task'].sudo().search(
            [('date_assign', '>', first_date), ('date_end', '<', last_date), ('user_ids', 'in', user.id)])
        qtrly = []
        for l in qtrly_tasks:
            qtrly.append(
                {
                    'task_id': l.id or 0,
                    'task_name': l.name or '',
                    'task_description': l.description or '',
                    'task_deadline': l.date_deadline.strftime("%d/%m/%Y") if l.date_deadline else '',
                    'task_start_date': l.date_assign.strftime("%d/%m/%Y %H:%M:%S") if l.date_assign else '',
                    'task_end_date': l.date_end.strftime("%d/%m/%Y %H:%M:%S") if l.date_end else '',
                    'total_time': l.effective_hours or 0.00,
                    'project_name': l.project_id.name or '',
                    'project_id': l.project_id.id or 0,
                    'status': l.stage_id.name or '',
                }
            )
        values = {
            'weekly': weekly,
            'monthly': month,
            'quarterly': qtrly
        }
        return valid_response(values, message='Project data has been fetched successfully', is_http=True)

    @validate_http_token
    @http_exception_handler
    @http.route(ROUTE_BASE + 'get_timesheet_day_wise', type="http", auth="public", methods=["GET"], csrf=False)
    def get_timesheet_day_wise(self, **payload):
        user = get_user(payload.get('user_id'))
        today = date.today()
        employee_id = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)])
        tasks = request.env['account.analytic.line'].sudo().search(
            [('employee_id', '=', employee_id.id), ('date', '=', today)])
        datas = []
        for i in tasks:
            result = '{0:02.0f}:{1:02.0f}'.format(*divmod(i.unit_amount * 60, 60))
            final = str(result) + ":00"
            if i.date == today:
                datas.append({
                    'date': i.date or '',
                    'task_id': i.task_id.id or 0,
                    'task_name': i.task_id.name or '',
                    'task_description': i.name or '',
                    'timesheet_id': i.id or 0,
                    'task_deadline': i.task_id.date_deadline.strftime("%d-%m-%Y") if i.task_id.date_deadline else '',
                    'start_date': i.date_start.strftime("%d-%m-%Y %H:%M:%S") if i.date_start else '',
                    'end_date': i.date_end.strftime("%d-%m-%Y %H:%M:%S") if i.date_end else '',
                    'planned_hours': i.task_id.planned_hours or 0.00,
                    'hours_spend': final or '',
                    'effective_hours': i.task_id.effective_hours or 0.00,
                    'status': i.task_id.stage_id.name or '',
                    'status_id': i.task_id.stage_id.id or 0,
                    'project_name': i.project_id.name or '',
                    'project_id': i.project_id.id or 0,
                    'approved_status': False,
                })
        yesterday = date.today() - timedelta(days=1)
        yesterday_tasks = request.env['account.analytic.line'].sudo().search(
            [('employee_id', '=', employee_id.id), ('date', '=', yesterday)])
        yesterday_datas = []
        for d in yesterday_tasks:
            result = '{0:02.0f}:{1:02.0f}'.format(*divmod(d.unit_amount * 60, 60))
            final = str(result) + ":00"
            if d.date == yesterday:
                yesterday_datas.append({
                    'date': d.date or '',
                    'task_id': d.task_id.id or 0,
                    'task_name': d.task_id.name or '',
                    'task_description': d.name or '',
                    'timesheet_id': d.id or 0,
                    'task_deadline': d.task_id.date_deadline.strftime("%d-%m-%Y") if d.task_id.date_deadline else '',
                    'start_date': d.date_start.strftime("%d-%m-%Y %H:%M:%S") if d.date_start else '',
                    'end_date': d.date_end.strftime("%d-%m-%Y %H:%M:%S") if d.date_end else '',
                    'planned_hours': d.task_id.planned_hours or 0.00,
                    'hours_spend': final or '',
                    'effective_hours': d.task_id.effective_hours or 0.00,
                    'status': d.task_id.stage_id.name or '',
                    'status_id': d.task_id.stage_id.id or 0,
                    'project_name': d.project_id.name or '',
                    'project_id': d.project_id.id or 0,
                    'approved_status': False,
                })
        secnd_day = date.today() - timedelta(days=2)
        secnd_tasks = request.env['account.analytic.line'].sudo().search(
            [('employee_id', '=', employee_id.id), ('date', '=', secnd_day)])
        secnd_datas = []
        for f in secnd_tasks:
            result = '{0:02.0f}:{1:02.0f}'.format(*divmod(f.unit_amount * 60, 60))
            final = str(result) + ":00"
            if f.date == secnd_day:
                secnd_datas.append({
                    'date': f.date or '',
                    'task_id': f.task_id.id or 0,
                    'task_name': f.task_id.name or '',
                    'task_description': f.name or '',
                    'timesheet_id': f.id or 0,
                    'task_deadline': f.task_id.date_deadline.strftime("%d-%m-%Y") if f.task_id.date_deadline else '',
                    'start_date': f.date_start.strftime("%d-%m-%Y %H:%M:%S") if f.date_start else '',
                    'end_date': f.date_end.strftime("%d-%m-%Y %H:%M:%S") if f.date_end else '',
                    'planned_hours': f.task_id.planned_hours or 0.00,
                    'hours_spend': final or '',
                    'effective_hours': f.task_id.effective_hours or 0.00,
                    'status': f.task_id.stage_id.name or '',
                    'status_id': f.task_id.stage_id.id or 0,
                    'project_name': f.project_id.name or '',
                    'project_id': f.project_id.id or 0,
                    'approved_status': True
                })
        third_day = date.today() - timedelta(days=3)
        third_tasks = request.env['account.analytic.line'].sudo().search(
            [('employee_id', '=', employee_id.id), ('date', '=', third_day)])
        third_datas = []
        for j in third_tasks:
            result = '{0:02.0f}:{1:02.0f}'.format(*divmod(j.unit_amount * 60, 60))
            final = str(result) + ":00"
            if j.date == third_day:
                third_datas.append({
                    'date': j.date or '',
                    'task_id': j.task_id.id or 0,
                    'task_name': j.task_id.name or '',
                    'task_description': j.name or '',
                    'timesheet_id': j.id or 0,
                    'task_deadline': j.task_id.date_deadline.strftime("%d-%m-%Y") if j.task_id.date_deadline else '',
                    'start_date': j.date_start.strftime("%d-%m-%Y %H:%M:%S") if j.date_start else '',
                    'end_date': j.date_end.strftime("%d-%m-%Y %H:%M:%S") if j.date_end else '',
                    'planned_hours': j.task_id.planned_hours or 0.00,
                    'hours_spend': final or '',
                    'effective_hours': j.task_id.effective_hours or 0.00,
                    'status': j.task_id.stage_id.name or '',
                    'status_id': j.task_id.stage_id.id or 0,
                    'project_name': j.project_id.name or '',
                    'project_id': j.project_id.id or 0,
                    'approved_status': True
                })
        final_day = date.today() - timedelta(days=4)
        final_tasks = request.env['account.analytic.line'].sudo().search(
            [('employee_id', '=', employee_id.id), ('date', '=', final_day)])
        final_datas = []
        for l in final_tasks:
            result = '{0:02.0f}:{1:02.0f}'.format(*divmod(l.unit_amount * 60, 60))
            final = str(result) + ":00"
            if l.date == final_day:
                final_datas.append({
                    'date': l.date or '',
                    'task_id': l.task_id.id or 0,
                    'task_name': l.task_id.name or '',
                    'task_description': l.name or '',
                    'timesheet_id': l.id or 0,
                    'task_deadline': l.task_id.date_deadline.strftime("%d-%m-%Y") if l.task_id.date_deadline else '',
                    'start_date': l.date_start.strftime("%d-%m-%Y %H:%M:%S") if l.date_start else '',
                    'end_date': l.date_end.strftime("%d-%m-%Y %H:%M:%S") if l.date_end else '',
                    'planned_hours': l.task_id.planned_hours or 0.00,
                    'hours_spend': final or '',
                    'effective_hours': l.task_id.effective_hours or 0.00,
                    'status': l.task_id.stage_id.name or '',
                    'status_id': l.task_id.stage_id.id or 0,
                    'project_name': l.project_id.name or '',
                    'project_id': l.project_id.id or 0,
                    'approved_status': True
                })

        values = {
            'user_id': user.id,
            'Today': datas,
            'Yesterday': yesterday_datas,
            '2nd previous day': secnd_datas,
            '3rd previous day': third_datas,
            '4th previous day': final_datas
        }
        return valid_response(values, message='Last 5 days Timesheet data has been fetched successfully', is_http=True)

    @validate_http_token
    @http_exception_handler
    @http.route(ROUTE_BASE + 'get_overdue_task', type="http", auth="public", methods=["GET"], csrf=False)
    def get_overdue_task(self, **payload):
        """Generates a new token for the passed user if no valid session found."""
        user = get_user(payload.get('user_id'))
        date_today = date.today()
        overdue_tasks = request.env['project.task'].sudo().search_count(
            [('user_ids', 'in', user.id), ('stage_id.is_closed', '=', False), ('date_deadline', '<', date_today)])
        progress_tasks = request.env['project.task'].sudo().search_count(
            [('user_ids', 'in', user.id), ('stage_id.is_open', '=', False), ('stage_id.is_closed', '=', False)])
        values = {
            'user_id': user.id,
            "overdue_tasks": overdue_tasks,
            "inprogress_tasks": progress_tasks
        }
        return valid_response(values, message='Overdue and Inprogress task count fetched successfully', is_http=True)

    @validate_http_token
    @http_exception_handler
    @http.route(ROUTE_BASE + 'get_holiday_status_id', type="http", auth="public", methods=["GET"], csrf=False)
    def get_overdue_task(self, **payload):
        """Generates a new token for the passed user if no valid session found."""
        user = get_user(payload.get('user_id'))
        leave_type = request.env['hr.leave.type'].sudo().search(
            [('requires_allocation', '=', 'no'), ('company_id', 'in', [False, user.employee_id.company_id.id])])
        l_type = []
        for i in leave_type:
            if i.requires_allocation == "yes":
                l_type.append({
                    'id': i.id or 0,
                    'name': i.name or '',

                    'remaining_leaves': (_('%g / %g')) % (
                        float_round(i.virtual_remaining_leaves, precision_digits=2) or 0.0,
                        float_round(i.max_leaves, precision_digits=2) or 0.0,
                    ) + (_(' hours') if i.request_unit == 'hour' else _(' days')),
                    'leave_validation_type': i.leave_validation_type,
                    'requires_attachment': i.support_document,
                    'requires_allocation': i.requires_allocation,
                })
            else:
                l_type.append({
                    'id': i.id or 0,
                    'name': i.name or '',
                    'requires_attachment': i.support_document,
                    'leave_validation_type': i.leave_validation_type,
                    'requires_allocation': i.requires_allocation,
                })
        return valid_response(l_type, message='Leave Type data fetched successfully', is_http=True)

    @validate_http_token
    @http_exception_handler
    @http.route(ROUTE_BASE + 'get_leave_allocation', type="http", auth="public", methods=["GET"], csrf=False)
    def get_leave_allocation(self, **payload):
        """Generates a new token for the passed user if no valid session found."""
        user = get_user(payload.get('user_id'))
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)])
        allocation = request.env['hr.leave.allocation'].sudo().search(
            [('employee_id', '=', employee.id), ('holiday_type', '=', 'employee'), ('date_to', '>', date.today())])
        allocate = []
        if allocation:
            for i in allocation:
                date_from = i.date_to.strftime("%d-%m-%Y")
                allocate.append({
                    'id': i.id or 0,
                    'name': i.name_validity or '',
                    'holiday_status_id': i.holiday_status_id.id or 0,
                    'allocation_type': i.allocation_type,
                    'date_from': i.date_from.strftime("%d-%m-%Y") or '',
                    'date_to': i.date_to.strftime("%d-%m-%Y") or '',
                    'mode': i.holiday_type,
                    'number_of_days_display': i.number_of_days_display or 0.00,
                })
        return valid_response(allocate, message='Leave Allocation data fetched successfully', is_http=True)

    @validate_http_token
    @http_exception_handler
    @http.route(ROUTE_BASE + 'get_pending_timeoff', type="http", auth="public", methods=["GET"], csrf=False)
    def get_pending_timeoff(self, **payload):
        """Generates a new token for the passed user if no valid session found."""
        user = get_user(payload.get('user_id'))
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)])
        leave = request.env['hr.leave'].sudo().search([('employee_id', '=', employee.id), ('state', '=', 'confirm')])
        allocate = []
        for i in leave:
            if i.state == 'confirm':
                state = "Pending"
            allocate.append({
                'id': i.id or 0,
                'name': i.name or '',
                'holiday_status_id': i.holiday_status_id.id or 0,
                'type_of_leave': i.holiday_status_id.name,
                'date_from': i.request_date_from.strftime("%d-%m-%Y") or '',
                'date_to': i.request_date_to.strftime("%d-%m-%Y") or '',
                'number_of_days_display': i.number_of_days or 0.00,
                'state': state
            })
        return valid_response(allocate, message='Leave Allocation data fetched successfully', is_http=True)

    @validate_http_token
    @http_exception_handler
    @http.route(ROUTE_BASE + 'get_complete_timeoff', type="http", auth="public", methods=["GET"], csrf=False)
    def get_complete_timeoff(self, **payload):
        """Generates a new token for the passed user if no valid session found."""
        user = get_user(payload.get('user_id'))
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)])
        leave = request.env['hr.leave'].sudo().search([('employee_id', '=', employee.id), ('state', '=', 'validate')])
        allocate = []
        for i in leave:
            if i.state == 'validate':
                state = "Completed"
            allocate.append({
                'id': i.id or 0,
                'name': i.name or '',
                'holiday_status_id': i.holiday_status_id.id or 0,
                'type_of_leave': i.holiday_status_id.name,
                'date_from': i.request_date_from.strftime("%d-%m-%Y") or '',
                'date_to': i.request_date_to.strftime("%d-%m-%Y") or '',
                'number_of_days_display': i.number_of_days or 0.00,
                'state': state
            })
        return valid_response(allocate, message='Leave Allocation data fetched successfully', is_http=True)

    # @validate_http_token
    # @http_exception_handler
    # @http.route(ROUTE_BASE + 'get_expense_categories', type="http", auth="public", methods=["GET"], csrf=False)
    # def get_expense_categories(self, **payload):
    #     """Generates a new token for the passed user if no valid session found."""
    #     user = get_user(payload.get('user_id'))

    @validate_http_token
    @http_exception_handler
    @http.route(ROUTE_BASE + 'get_announcement', type="http", auth="public", methods=["GET"], csrf=False)
    def get_announcement(self, **payload):
        """Generates a new token for the passed user if no valid session found."""
        user = get_user(payload.get('user_id'))
        announcement = request.env['kg.announcement'].sudo().search([('user_id', '=', user.id)])
        event = []
        for i in announcement:
            event.append({
                'id': i.id or 0,
                'name': i.name or '',
                'type': i.type_id.id or '',
                'description': i.description or '',
                'image': i.image_1920 if i.image_1920 else '',

            })
        return valid_response(event, message='Announcement data fetched successfully', is_http=True)

    @validate_http_token
    @http_exception_handler
    @http.route(ROUTE_BASE + 'get_expense', type="http", auth="public", methods=["GET"], csrf=False)
    def get_expense(self, **payload):
        """Generates a new token for the passed user if no valid session found."""
        user = get_user(payload.get('user_id'))
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)])
        draft = request.env['kg.expense'].sudo().search(
            [('employee_id', '=', employee.id), ('state', '=', 'draft')])
        expense_draft = []
        for ed in draft:
            expense_draft.append({
                'id': ed.id or 0,
                'number': ed.number or '',
                'name': ed.name or '',
                'date': ed.expense_date.strftime("%d-%m-%Y"),
                'total': sum(ed.expense_line_ids.mapped('cost')),
                'currency': ed.currency_id.id or '',
                'description': ed.name or '',
                'state': ed.state

            })
        waiting = request.env['kg.expense'].sudo().search(
            [('employee_id', '=', employee.id), ('state', '=', 'waiting')])
        expense_waiting = []
        for wait in waiting:
            expense_waiting.append({
                'id': wait.id or 0,
                'number': wait.number or '',
                'name': wait.name or '',
                'date': wait.expense_date.strftime("%d-%m-%Y"),
                'total': sum(wait.expense_line_ids.mapped('cost')),
                'currency': wait.currency_id.id or '',
                'description': wait.name or '',
                'state': wait.state

            })
        approve = request.env['kg.expense'].sudo().search(
            [('employee_id', '=', employee.id), ('state', '=', 'approved')])
        expense_approve = []
        for apprve in approve:
            expense_approve.append({
                'id': apprve.id or 0,
                'number': apprve.number or '',
                'name': apprve.name or '',
                'date': apprve.expense_date.strftime("%d-%m-%Y"),
                'total': sum(apprve.expense_line_ids.mapped('cost')),
                'currency': apprve.currency_id.id or '',
                'description': apprve.name or '',
                'state': apprve.state

            })

        refused = request.env['kg.expense'].sudo().search(
            [('employee_id', '=', employee.id), ('state', '=', 'refused')])
        expense_refused = []
        for reject in refused:
            expense_refused.append({
                'id': reject.id or 0,
                'number': reject.number or '',
                'name': reject.name or '',
                'date': reject.expense_date.strftime("%d-%m-%Y"),
                'total': sum(reject.expense_line_ids.mapped('cost')),
                'currency': reject.currency_id.id or '',
                'description': reject.name or '',
                'state': reject.state

            })
        cancel = request.env['kg.expense'].sudo().search(
            [('employee_id', '=', employee.id), ('state', '=', 'cancel')])
        expense_cancel = []
        for c in cancel:
            expense_cancel.append({
                'id': c.id or 0,
                'number': c.number or '',
                'name': c.name or '',
                'date': c.expense_date.strftime("%d-%m-%Y"),
                'total': sum(c.expense_line_ids.mapped('cost')),
                'currency': c.currency_id.id or '',
                'description': c.name or '',
                'state': c.state

            })
        values = {
            'draft': expense_draft,
            'waiting': expense_waiting,
            'approve': expense_approve,
            'reject': expense_refused,
            'cancel': expense_cancel,
        }
        return valid_response(values, message='Expense data fetched successfully', is_http=True)

    @validate_http_token
    @http_exception_handler
    @http.route(ROUTE_BASE + 'get_expense_category', type="http", auth="public", methods=["GET"], csrf=False)
    def get_expense_category(self, **payload):
        """Generates a new token for the passed user if no valid session found."""
        expense_category_list = request.env['kg.expense.category'].sudo().search([])
        category = []
        for i in expense_category_list:
            category.append({
                'id': i.id or 0,
                'name': i.category_name or '',
                # 'cost': i.cost or '',
                'internal_ref': i.internal_ref or '',
            })
        return valid_response(category, message='Expense Category data fetched successfully', is_http=True)

    @validate_http_token
    @http_exception_handler
    @http.route(ROUTE_BASE + 'get_currency', type="http", auth="public", methods=["GET"], csrf=False)
    def get_currency(self, **payload):
        """Generates a new token for the passed user if no valid session found."""
        get_currency = request.env['res.currency'].sudo().search([])
        currency = []
        for i in get_currency:
            currency.append({
                'id': i.id or 0,
                'name': i.name or '',
                'symbol': i.symbol or '',
            })
        return valid_response(currency, message='Currency data fetched successfully', is_http=True)

    @validate_http_token
    @http_exception_handler
    @http.route(ROUTE_BASE + 'get_employee', type="http", auth="public", methods=["GET"], csrf=False)
    def get_employee(self, **payload):
        """Generates a new token for the passed user if no valid session found."""
        department = payload.get('department_id')
        department_id = request.env['hr.department'].search([('id', '=', department)])
        employee_list = []
        all_employee_list = []

        if department_id.id:
            for dept in department_id:
                get_employee = request.env['hr.employee'].sudo().search([('department_id', '=', dept.id)])
                for i in get_employee:
                    employee_list.append({
                        'id': i.id or 0,
                        'name': i.name or '',
                        'department': i.department_id.id or 0,
                        'department_name': i.department_id.name or ''

                    })
        else:
            get_employee = request.env['hr.employee'].sudo().search([])
            for i in get_employee:
                all_employee_list.append({
                    'id': i.id or 0,
                    'name': i.name or '',
                    'department': i.department_id.id,
                    'department_name': i.department_id.name

                })
        values = {
            "employee_department_wise": employee_list,
            "all_employee": all_employee_list
        }

        return valid_response(values, message='Employee data fetched successfully', is_http=True)

    @validate_http_token
    @http_exception_handler
    @http.route(ROUTE_BASE + 'get_department', type="http", auth="public", methods=["GET"], csrf=False)
    def get_department(self, **payload):
        """Generates a new token for the passed user if no valid session found."""
        department = request.env['hr.department'].sudo().search([])
        department_list = []
        for i in department:
            department_list.append({
                'id': i.id or 0,
                'name': i.name or '',

            })
        return valid_response(department_list, message='Department data fetched successfully', is_http=True)

    @validate_http_token
    @http_exception_handler
    @http.route(ROUTE_BASE + 'get_helpdesk_category', type="http", auth="public", methods=["GET"], csrf=False)
    def get_helpdesk_category(self, **payload):
        """Generates a new token for the passed user if no valid session found."""
        helpdesk_category = request.env['helpdesk.ticket.category'].sudo().search([])
        category_list = []
        for i in helpdesk_category:
            category_list.append({
                'id': i.id or 0,
                'name': i.name or '',

            })
        return valid_response(category_list, message='Helpdesk Category data fetched successfully', is_http=True)

    @validate_http_token
    @http_exception_handler
    @http.route(ROUTE_BASE + 'get_helpdesk', type="http", auth="public", methods=["GET"], csrf=False)
    def get_helpdesk(self, **payload):
        """Generates a new token for the passed user if no valid session found."""
        helpdesk = request.env['helpdesk.ticket'].sudo().search([])
        ticket = request.env['helpdesk.ticket.stage'].search([])
        sort = ticket.sorted(key='sequence')
        stage = {}
        for j in sort:
            helpdesk_ticket = helpdesk.filtered(lambda x: x.stage_id == j)
            helpdesk_list = []
            for i in helpdesk_ticket:
                helpdesk_list.append({
                    'id': i.id or 0,
                    'number': i.number or '',
                    'name': i.name or '',
                    'team': i.team_id.name or '',
                    'create_date': i.create_date.strftime("%d-%m-%Y"),
                    'user': i.user_id.name or '',
                    'company': i.company_id.name or '',
                    'category': i.category_id.name or "",
                    "project": i.project_id.name or '',
                    "task": i.task_id.name or '',
                    "state": i.stage_id.name or ''

                })
            values = {j.name: helpdesk_list}
            stage.update(values)
            # stage[j.name].append(helpdesk_list)
            # values = {
            #     'stage': stage,
            #     'stage_name': j,
            #
            # }
        return valid_response(stage, message='Helpdesk data fetched successfully', is_http=True)

    @validate_http_token
    @http_exception_handler
    @http.route(ROUTE_BASE + 'get_employee_details', type="http", auth="public", methods=["GET"], csrf=False)
    def get_employee_details(self, **payload):
        """Fetch employee details by name with image."""
        name = payload.get('name')
        if not name:
            return invalid_response("missing_name", "Missing 'name' in request payload", 400)

        employees = request.env['hr.employee'].sudo().search([('name', 'ilike', name)])
        print(employees,'dddddddddd')
        result = []
        for emp in employees:
            # image_base64 = base64.b64encode(emp.image_1920).decode('utf-8') if emp.image_1920 else ''
            image_base64 = _convert_image_to_base64(
                emp.image_128) or '',
            result.append({
                'id': emp.id,
                'name': emp.name,
                'job_title': emp.job_title,
                'work_email': emp.work_email,
                'department': emp.department_id.name if emp.department_id else '',
                'image': image_base64
            })

        return valid_response(result, message="Employee details fetched successfully", is_http=True)

    @validate_http_token
    @http_exception_handler
    @http.route(ROUTE_BASE + 'get_attendance', type="http", auth="public", methods=["GET"], csrf=False)
    def get_attendance(self, **params):
        """Fetch employee details by name with image and timezone."""
        print("payload", params)
        employee_id = params.get('employee_id')
        start_date = params.get('start_date')
        end_date = params.get('end_date')

        # Validate required parameter
        if not employee_id:
            return {"error": "Missing employee_id parameter"}

        # Fetch employee record for timezone
        employee = request.env['hr.employee'].sudo().browse(int(employee_id))
        employee_timezone = employee.user_id.tz or 'UTC'

        domain = [('employee_id', '=', int(employee_id))]
        if start_date:
            domain.append(('check_in', '>=', start_date))
        if end_date:
            domain.append(('check_in', '<=', end_date))

        records = request.env['hr.attendance'].sudo().search(domain)
        result = []
        today_str = fields.Date.today().isoformat()
        for rec in records:
            is_today = rec.check_in and rec.check_in.date().isoformat() == today_str
            result.append({
                'id': rec.id,
                'employee_id': rec.employee_id.id,
                'employee_name': rec.employee_id.name,
                'check_in': rec.check_in,
                'check_out': None if (is_today and not rec.check_out) else rec.check_out,
                'worked_hours': rec.worked_hours,
                'timezone': employee_timezone,
            })
        return valid_response(result, message="Employee attendence fetched successfully", is_http=True)
