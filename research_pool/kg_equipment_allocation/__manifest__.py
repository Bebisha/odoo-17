# -*- coding: utf-8 -*-

# Klystron Global LLC
# Copyright (C) Klystron Global LLC
# All Rights Reserved
# https://www.klystronglobal.com/


{
    'name': 'Equipment Allocation',
    'summary': """
        Employee can make Equipment Allocation Request for the Equipment.""",
    'description': """
           Employee can make Equipment Allocation Request for the Equipment.""",
    'author': 'Klystron Global',
    'maintainer':'Bebisha C P',
    'website': "https://www.klystronglobal.com/",
     'category': 'HR',
    'version': '17.0.0.1',
    'license': 'AGPL-3',
    'depends': ['base', 'hr','maintenance','mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/equipment_allocation_views.xml',
        'views/hr_employee_views.xml',
        'views/equipment_allocaton_request_views.xml',
    ],

}
