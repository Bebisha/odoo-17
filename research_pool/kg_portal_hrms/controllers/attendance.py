from odoo import http, fields
from odoo.http import request
from datetime import datetime, timedelta, timezone, date
from odoo.addons.portal.controllers.portal import CustomerPortal, pager
from datetime import datetime
import pytz

from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class AttendancePortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        vcc = super()._prepare_home_portal_values(counters)
        # print(vcc, 'ffffffffffffffff')
        vcc['att_count'] = request.env['hr.attendance'].search_count([])
        return vcc

    @http.route(['/my/attendance'], type='http', auth="user", website=True)
    def portal_attendance_page(self, **kw):
        user = request.env.user
        return request.render('kg_portal_hrms.attendance_template', {
            'user': user
        })

    @http.route(['/my/attendance/checkin'], type='http', auth="user", methods=['POST'])
    def checkin(self, **kw):
        user = request.env.user
        if user.employee_id:
            employee = user.employee_id
            if employee.attendance_state != 'checked_in':
                emp = request.env['hr.attendance'].sudo().create({
                    'employee_id': employee.id,
                    'check_in': fields.Datetime.now(),
                })
                print(emp.check_in, '90000000)()')
                employee.write({'attendance_state': 'checked_in'})
        return request.redirect('/my/attendance')

    @http.route(['/my/attendance/checkout'], type='http', auth="user", methods=['POST'])
    def checkout(self, **kw):
        user = request.env.user
        if user.employee_id:
            employee = user.employee_id
            attendance = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee.id),
                ('check_out', '=', False)
            ], limit=1, order='check_in desc')
            print(attendance.check_out, 'ewwwwwwwwwwww)()')

            if attendance:
                attendance.write({'check_out': fields.Datetime.now()})
                employee.write({'attendance_state': 'checked_out'})
        return request.redirect('/my/attendance')

    def convert_to_user_time(self, time, env):
        local_tz = pytz.timezone(env.user.partner_id.tz)
        current_date = date.today()
        utc_time = datetime.combine(current_date, time, tzinfo=pytz.UTC)
        local_time = utc_time.astimezone(local_tz)
        time_result = local_time.strftime("%m-%d-%Y %H:%M:%S")
        return time_result

    @http.route('/employee/attendance', type='http', website=True, auth="user")
    def PortalEmployeeAttendance(self, **kw):
        attend = request.env['hr.attendance'].sudo().search([])
        attend_list = []
        for rec in attend:
            check_in_local = self.convert_to_user_time(rec.check_in.time(), request.env)
            check_out_local = self.convert_to_user_time(rec.check_out.time(), request.env)
            attend_list.append({
                'record': rec,
                'check_in_local': check_in_local,
                'check_out_local': check_out_local,
                'employee_name': rec.employee_id.name,
            })
        vals = {'attend': attend_list}
        return request.render('kg_portal_hrms.portal_emp_attendance_list_view', vals)

