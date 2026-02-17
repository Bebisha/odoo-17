# -*- coding: utf-8 -*-

# Klystron Global LLC
# Copyright (C) Klystron Global LLC
# All Rights Reserved
# https://www.klystronglobal.com/
{
    'name': "Kg Casio Ticket",
    'version': '17.0.1.0.0',
    'summary': """ Casio Ticket""",
    'description': """Casio Ticket""",
    'author': 'Klystron Global',
    'maintainer': 'Klystron Global',
    'depends': ['portal', 'mail', 'base', 'crm', 'helpdesk', 'kg_casio'],
    'data': [
        'security/ir.model.access.csv',
        'data/helpdesk_stage.xml',
        'wizard/cs_hq_report_view.xml',
        'views/helpdesk_stage_views.xml',
        'views/helpdesk_ticket_view.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
