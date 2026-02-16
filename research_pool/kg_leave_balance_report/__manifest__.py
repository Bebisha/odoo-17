# -*- coding: utf-8 -*-

# Klystron Global LLC
# Copyright (C) Klystron Global LLC
# All Rights Reserved
# https://www.klystronglobal.com/


{
    'name': 'Leave Balance Report',
    'summary': 'Allocated balance, taken leaves and remaining balance per leave type for each employee',
    'description': """User Can view Allocated balance, taken leaves and remaining balance per leave type for each employee""",
    'author': 'Klystron Global',
    'maintainer':'Bebisha C P',
    'website': "https://www.klystronglobal.com/",
    'category': 'Human Resources/Time Off',
    'version': '17.0.0.1',
    'license': 'LGPL-3',
    'depends': ['hr', 'hr_holidays'],
    'data': [
        'security/ir.model.access.csv',

        'views/employee_leave_views.xml',

    ],
}


