# -*- coding: utf-8 -*-
{
    'name': "KG helpdesk Management",
    'version': '17.0.1.0.0',
    'depends': ['base', 'helpdesk_mgmt', 'project','kg_success_pack'],
    'author': 'Klystron',
    'description': "helpdesk management customisation",
    'maintainer': "Ashvad",
    'category': 'heldesk/management',
    'data': [
        'wizard/mail_activity_schedule.xml',
        'views/helpdesk_ticket_view.xml',
        'views/project_task_view.xml',
    ],

    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False
}
