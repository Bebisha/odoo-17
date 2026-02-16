# -*- coding: utf-8 -*-

# Klystron Global LLC
# Copyright (C) Klystron Global LLC
# All Rights Reserved
# https://www.klystronglobal.com/
{
    'name': "Teacher Registration",
    'version': '17.0.1.0.0',
    'category': 'Website',
    'summary': """ Teacher Registration""",
    'description': """Teacher Registration""",
    'author': 'Klystron Global',
    'maintainer': 'Bebisha',
    'depends': ['website', 'portal', 'mail'],
    'data': [
         'data/ir_cron.xml',
        'security/ir.model.access.csv',
        'data/portal_registration_menu.xml',
        'views/porat_registration_form_view.xml',
        'views/menu.xml',
        'views/emulator_licence_views.xml',
        'views/teacher_registration_views.xml',
        'views/terms_conditions_template.xml',
        'views/conf_setting_views.xml',
        'views/icon_template.xml',
        'wizards/import_license_date_view.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
