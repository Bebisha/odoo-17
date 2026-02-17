# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'KG Sales Tracker',
    'version': '17.0.1.0.0',
    'category': '',
    'summary': '',
    'description': """KG Leads""",
    'depends': ['crm'],
    'data': [
'security/groups.xml',
        'security/ir.model.access.csv',

        'data/data.xml',
        'views/res_users.xml',
        'views/sales_target_views.xml',
        'views/kg_sales_tracker_views.xml',
        'views/revenue_head_views.xml',
        'views/menu.xml',
    ],

    'sequence': -1,
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
