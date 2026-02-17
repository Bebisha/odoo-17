# -*- encoding: utf-8 -*-

{
    'name': 'Employee Dashboard',
    'version': '17.0.1.0.0',
    'category': 'Employee Dashboard',
    'author': 'Klystron Global',
    'description': """Employee Dashboard""",
    'summary': '',
    'website': 'www.klystronglobal.com',
    # 'images': ['static/description/icon.png'],
    'data': [
        # 'security/ir.model.access.csv',
        'view/employee_dashboard_views.xml',
        'view/hr_employee_views.xml',

    ],
    'depends': ['base', 'website', 'website_sale', 'project',
                'portal', 'web', 'hr',
                ],
    'assets': {
        'web.assets_backend': [
            'kg_employee_dashboard/static/src/js/employee_dashboard.js',
            'kg_employee_dashboard/static/src/xml/employee_dashboard_template.xml',
        ],
    },

    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 105,
    'license': 'AGPL-3',
}
