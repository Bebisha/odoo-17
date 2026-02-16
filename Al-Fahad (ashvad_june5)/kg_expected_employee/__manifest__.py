# -*- coding: utf-8 -*-
{
    'name': "Employee Form",

    "summary": "Employee Form",
    "version": "17.0.1.0.0",
    'category': 'hr',
    "license": "OPL-1",
    'depends': ['hr','sale','website_sale_checkout_skip_payment' ],

    'data': [
        'security/ir.model.access.csv',
        'views/expected_employee.xml',
        'views/employee_department.xml',
        # 'views/website_sale_inherit.xml',
        'views/sale_order_views.xml',

    ],

}
