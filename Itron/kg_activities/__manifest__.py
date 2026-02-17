# -*- coding: utf-8 -*-
{
    'name': "KG Activities",
    'version': '17.0.1.0.0',
    'depends': ['base','mail','project'],
    'author': 'klystron',
    'description': "customization mail activity",
    'maintainer': "klystron",
    'category': 'mail/activity',

    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/mail_acivity_history_views.xml',
        'views/menus.xml',

    ],

    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False
}
