# -*- coding: utf-8 -*-

# Klystron Global LLC
# Copyright (C) Klystron Global LLC
# All Rights Reserved
# https://www.klystronglobal.com/


{
    'name': 'Quick Sale Order To Purchase Order',
    'summary': """
         Quick Sale Order To Purchase Order""",
    'description': """
            Quick Sale Order To Purchase Order""",
    'author': 'Klystron Global',
    'maintainer':'Bebisha C P',
    'website': "https://www.klystronglobal.com/",
     'category': 'HR',
    'version': '17.0.0.1',
    'license': 'AGPL-3',
    'depends': ['base', 'sale','purchase'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/purchase_views.xml',
        'views/saleorder_views.xml',

    ],
    # 'assets': {
    #     'web.assets_backend': [
    #         'kg_hr_dashboard/static/src/js/dashboard.js',
    #         'kg_hr_dashboard/static/src/xml/dashboard.xml',
    #         'kg_hr_dashboard/static/src/css/dashboard.css',
    #
    #     ],
    # },
}
