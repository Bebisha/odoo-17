# -*- coding: utf-8 -*-

# Klystron Global LLC
# Copyright (C) Klystron Global LLC
# All Rights Reserved
# https://www.klystronglobal.com/

{
    'name': 'Kg Time Off',
    'version': '17.0.1.0.0',
    'license': 'LGPL-3',
    'depends': ['base','hr','hr_holidays','quality_control'],
    'sequence': '-100',
    'category': '',
    'author': 'Klystron Global',
    'maintainer': 'Klystron Global',
    'website': "www.klystronglobal.com",
    'application': True,
    'description': """The Module provide custom tax invoice""",
    'data': [
        'data/activity.xml',
        'views/hr_leave_views.xml',
        # 'views/hr_leave_type.xml',
        'views/res_config_settings_views.xml',
        'views/workshee_template.xml'

    ],


    "installable": True,
    'demo': [],

}