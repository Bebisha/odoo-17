from odoo import http, fields
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager


class ExpensePortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        amp = super()._prepare_home_portal_values(counters)
        amp['exp_count'] = request.env['hr.expense'].search_count([])
        return amp

    @http.route('/my/expense', type='http', auth="user", website=True)
    def portal_expense_form(self, **kw):
        exp_type = request.env['product.product'].sudo().search([('can_be_expensed', '=', True)])
        user = request.env.user
        values = {
            'employee_id': user if user else '',
            'exp_type': exp_type,
        }
        print(values, "qwqwqqqwq")
        return request.render('kg_portal_hrms.expense_portal_form', values)

    @http.route('/submit_expense', type='http', auth='user', methods=['POST'], website=True, csrf=False)
    def submit_expense(self, **post):
        print(post, 'jjjjjjjjjjjjjjjjjjjjj')

        emp_id = post.get('emp_id')
        name = post.get('name')
        product_id = post.get('product_id')
        product = request.env['product.product'].sudo().search([('name', '=', product_id)])

        employee = request.env['hr.employee'].sudo().search([('user_id', '=', int(emp_id))])
        print(employee, 'bbbbbbbbbbbbbbbbb')

        total_amount_currency = post.get('total_amount_currency')
        date = post.get('date')

        exx = request.env['hr.expense'].sudo().create({
            'employee_id': employee.id,
            'name': name,
            'product_id': product.id,
            'total_amount_currency': total_amount_currency,
            'date': date,
        })
        print(exx.name, "EDA mwonee")
        # print(exx.total_amount_currency,"EDA mwonee")
        # print(exx.date,"EDA mwonee")

        return request.redirect('/portal/expense/thank_you')

    @http.route('/portal/expense/thank_you', type='http', auth='user', website=True)
    def thank_you(self, **kwargs):
        return request.render('kg_portal_hrms.expense_portal_thanks')

    # Portal List View

    @http.route('/employee/expense', type='http', website=True, auth="user", )
    def PortalEmployeeAExpense(self, **kw):
        exp_amnt = request.env['hr.expense'].sudo().search([])
        vals = {'exp_amnt': exp_amnt}

        return request.render('kg_portal_hrms.portal_expense_listview', vals)
