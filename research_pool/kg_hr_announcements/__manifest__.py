# -*- coding: utf-8 -*-

# Klystron Global LLC
# Copyright (C) Klystron Global LLC
# All Rights Reserved
# https://www.klystronglobal.com/


{
    'name': 'Announcements',
    'summary': """
        Managing Official Announcements""",
    'description': """
           This module helps you to manage hr official announcements""",
    'author': 'Klystron Global',
    'maintainer':'Bebisha C P',
    'website': "https://www.klystronglobal.com/",
    'category': 'Human Resources',
    'version': '17.0.0.1',
    'license': 'LGPL-3',
    'depends': ['base', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_announcement_views.xml',
        'views/hr_employee_views.xml',
        'views/hr_dashboard.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'kg_hr_announcements/static/src/js/dashboard.js',
            'kg_hr_announcements/static/src/xml/dashboard.xml',

        ],
    },
}

