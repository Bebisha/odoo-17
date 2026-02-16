from odoo.addons.portal.controllers.portal import CustomerPortal, pager
from odoo import http
from odoo.http import request


class PortalTimeOff(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        cvv = super()._prepare_home_portal_values(counters)
        cvv['time_count'] = request.env['employee.time_off'].search_count([])
        return cvv

    @http.route('/portal/time_off_form', type='http', auth='user', website=True)
    def time_off_form(self, **kwargs):
        leave_types = request.env['hr.leave.type'].sudo().search([])
        print(leave_types, "gggggggggggggggggggggggggg")

        user = request.env.user
        values = {
            'employee_id': user.name if user else '',
            'leave_types': leave_types,
        }
        return request.render('kg_portal_hrms.portal_time_off_form', values)

    @http.route('/portal/time_off_form/submit', type='http', auth='user', methods=['POST'], website=True, csrf=False)
    def submit_time_off_form(self, **post):
        employee_id = post.get('employee_id')
        start_date = post.get('start_date')
        holiday_status_id = post.get('holiday_status_id')
        number_of_days_display = post.get('number_of_days_display')
        end_date = post.get('end_date')
        reason = post.get('reason')

        x = request.env['employee.time_off'].sudo().create({
            'employee_id': employee_id,
            'start_date': start_date,
            'holiday_status_id': holiday_status_id,
            'number_of_days_display': number_of_days_display,
            'end_date': end_date,
            'reason': reason,
        })
        print(x.employee_id, '(((((())))))')

        return request.redirect('/portal/timeoff_form/thank_you')

    @http.route('/portal/timeoff_form/thank_you', type='http', auth='user', website=True)
    def thank_you_time_off(self, **kwargs):
        return request.render('kg_portal_hrms.timeoff_portal_thanks')

    @http.route('/employee/timeoff', type='http', website=True)
    def PortalEmployeeTimeoff(self, search="", search_in="All", **kw):
        search_list = {
            'All': {'label': 'All', 'input': 'All', 'domain': []},
            'Employee': {'label': 'Employee', 'input': 'Employee', 'domain': [('employee_id.name', 'ilike', search)]}
        }
        search_domain = search_list[search_in]['domain']

        emp_timeoff = request.env['employee.time_off']
        timeoff = emp_timeoff.search([])
        vals = {'timeoff': timeoff, 'page_name': 'employee_list_view', 'search_in': search_in,
                'searchbar_inputs': search_list
            , 'search': search}
        print(timeoff, "gfgfgf")
        return request.render('kg_portal_hrms.portal_timeoff_listview', vals)

    @http.route(['/my/employee_time_off/<model("employee.time_off"):employee_id>'], type='http', website=True)
    def PortalEmployeeTimeoffFormView(self, employee_id, **kw):
        vals = {"employee": employee_id, }
        vendor_obj = request.env['employee.time_off'].search([])
        vendor_ids = vendor_obj.ids
        vendor_index = vendor_ids.index(employee_id.id)
        print(vendor_index, "yyyyyy")

        return request.render("kg_portal_hrms.vendors_form_view_portal", vals)
