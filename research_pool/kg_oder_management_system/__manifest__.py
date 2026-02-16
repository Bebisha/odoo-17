# -*- coding: utf-8 -*-

# Klystron Global LLC
# Copyright (C) Klystron Global LLC
# All Rights Reserved
# https://www.klystronglobal.com/


{
    'name': 'Order Management System',
    'summary': 'Sale order management sysytem ',
    'description': """Sale order management sysytem """,
    'author': 'Klystron Global',
    'maintainer':'Bebisha C P',
    'website': "https://www.klystronglobal.com/",
    'category': 'sale',
    'version': '17.0.0.1',
    'license': 'LGPL-3',
    'depends': ['sale','sale_management','base'],
     'data': [
        'views/custom_sale_dashboard_views.xml',

    ],
    'assets': {
        'web.assets_backend': [
            'kg_oder_management_system/static/src/**/*',
        ],
    },

}


