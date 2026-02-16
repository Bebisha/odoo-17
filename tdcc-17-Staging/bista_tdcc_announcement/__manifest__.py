# -*- coding: utf-8 -*-
#############################################################################
# -*- encoding: utf-8 -*-
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
#############################################################################


{
    'name': 'TDCC Official Announcements',
    'version': "17.1.1",
    'summary': """Managing Official Announcements""",
    'description': 'This module helps you to manage hr official announcements',
    'category': 'Human Resources',
    'author': 'Bista Solutions Inc.',
    'website': "https://www.bistasolutions.com",
    'depends': ['base', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_announcement_view.xml',
    ],
    'demo': [],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    # 'auto_install': False,
    'application': True,
}
