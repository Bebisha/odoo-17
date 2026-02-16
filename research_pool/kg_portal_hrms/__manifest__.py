{
    'name': "Portal HRMS",
    'version': '17.0.1.0.0',
    'category': 'Website',
    'summary': """Employee Portal HRMS""",
    'description': """Employee Portal HRMS""",
    'author': 'Klystron Global',
    'maintainer': 'Abhiram',
    'depends': ['hr_holidays', 'website', 'hr', 'contacts', 'portal','hr_attendance','hr_expense'],
    'data': [
        'security/ir.model.access.csv',
        # 'security/ir_rule.xml',
        'views/timeoff_employee_portal_form_temp.xml',
        'views/employee_timeoffdata_menu.xml',
        'views/timeoff_portal_template_listview.xml',
        'views/attendance_template.xml',
        'views/expense_portal_template.xml',
        'views/expense_portal_list_view.xml',

        'data/portal_registration_menu.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'kg_portal_hrms/static/src/js/portal.js',
            # 'kg_portal_hrms/static/src/js/hide.js',
            # 'kg_portal_hrms/static/src/js/attendance.js',
        ],
    },
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
