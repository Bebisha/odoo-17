# -*- coding: utf-8 -*-

# Klystron Global LLC
# Copyright (C) Klystron Global LLC
# All Rights Reserved
# https://www.klystronglobal.com/


{
    'name': 'HR Dashboard',
    'summary': """
         HR Dashboard""",
    'description': """
            HR Dashboard""",
    'author': 'Klystron Global',
    'maintainer':'Bebisha C P',
    'website': "https://www.klystronglobal.com/",
     'category': 'HR',
    'version': '17.0.0.1',
    'license': 'AGPL-3',
    'depends': ['base', 'hr', 'event', 'board','crm'],
    'data': [
        'views/dashboard_views.xml',

    ],
    'assets': {
        'web.assets_backend': [
            'kg_hr_dashboard/static/src/js/dashboard.js',
            'kg_hr_dashboard/static/src/xml/dashboard.xml',
            'kg_hr_dashboard/static/src/css/dashboard.css',

        ],
    },
}

