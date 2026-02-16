# -*- coding: utf-8 -*-

# Klystron Global LLC
# Copyright (C) Klystron Global LLC
# All Rights Reserved
{
    'name': 'CRM',
    'summary': """
       CRM""",
    'description': """
       CRM """,
    'author': 'Klystron Global',
    'maintainer': 'Bebisha C P',
    'website': "https://www.klystronglobal.com/",
    'category': 'CRM',
    'version': '17.0.0.1',
    'license': 'AGPL-3',
    'depends': ['crm', 'base', 'sales_team', 'crm_iap_mine','sale'],
    'data': [
        'views/crm_views.xml',

    ],
    'assets': {
        'web.assets_backend': [
            'kg_crm/static/src/*/',


        ],
    },
}
