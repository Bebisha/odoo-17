# -*- coding: utf-8 -*-
###############################################################################
{
    'name': 'Stock Report Reordering',
    'version': '17.0.1.0.0',
    'summary': 'Stock Report Reordering Action',
    'description': """The module helps to run reordering action 
    if stock reaches minimum quantity.""",
    'category': 'Inventory/Inventory',
    'author': "Klystron Global",
    'maintainer': 'Klystron Global',
    'company': 'Klystron Global',
    'depends': [
        'base',
        'stock',
        'purchase',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_inventory.xml',
        'wizard/wizard_create_frq_views.xml',

    ],
    'assets': {
        # 'web.assets_backend': [
        #     'ent_uae_wps_report/static/src/js/action_manager.js',
        # ],
    },
    'license': 'OPL-1',
    'installable': True,
    'application': False,
    'auto_install': False,
}
