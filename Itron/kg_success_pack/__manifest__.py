# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'KG Success Pack',
    'version': '17.0.1.0.0',
    'category': '',
    'summary': '',
    'description': """Success packs under projects""",
    'depends': ['project', 'hr_timesheet', 'kg_timeoff_dashboard', 'hr', 'sale'],
    'data': [
        'security/ir.model.access.csv',
        'security/groups.xml',
        'data/packs.xml',
        'data/email_template.xml',
        'data/sequence.xml',
        'reports/template.xml',
        'views/pack_timesheet.xml',

        'views/task.xml',
        'views/project.xml',
        'views/sale_order_view.xml',
        'views/success_pack.xml',
        'views/pack_projects.xml',
        'views/dashboard_menu.xml',

        'views/product_view.xml',
    ],

    "assets": {
        "web.assets_backend": [
            'kg_success_pack/static/src/js/success_pack_dashboard.js',
            'kg_success_pack/static/src/xml/success_pack_dashboard.xml',

        ]

    },
    'sequence': -1,
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
