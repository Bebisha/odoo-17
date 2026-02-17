# -*- coding: utf-8 -*-
{
    'name': "KG Voyage Marine Asset",

    "summary": "Customization for Asset",
    "version": "17.0.1.0.0",
    'category': 'Accounting',
    'author': "Klystron Global",
    'maintainer': "SUMAYYA P P",
    "license": "OPL-1",
    'website': 'https://www.klystronglobal.com',
    'depends': ['base', 'account', 'account_asset', 'project'],
    'data': [
        'security/ir.model.access.csv',
        'security/groups.xml',
        'data/sequence.xml',
        'views/account_asset_views.xml',
        'views/maintenance_equipment_view.xml',
    ],

}
