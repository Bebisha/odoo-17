# -*- coding: utf-8 -*-

{
    'name': 'Kg Project Dashboard',
    'category': 'project',
    'summary': 'Detailed Dashboard View for Project',
    'description': 'Detailed Dashboard View for Project',
    'version': '17.0.1.0.0',
    'website': 'https://www.cybrosys.com',
    'license': 'LGPL-3',
    'depends': [
        'project', 'project_task_analysis'
    ],
    'data': [
        'views/dashboard_views.xml',
        'views/project_task_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'kg_dashboard_odoo/static/src/css/dashboard.css',
            "kg_dashboard_odoo/static/src/js/dashboard.js",
            'kg_dashboard_odoo/static/src/xml/dashboard.xml',
        ],
        # 'web.assets_qweb': [
        #     'kg_dashboard_odoo/static/src/xml/dashboard.xml',
        # ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
