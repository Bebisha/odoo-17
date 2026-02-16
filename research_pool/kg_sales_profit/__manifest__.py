# -*- coding: utf-8 -*-

# Klystron Global LLC
# Copyright (C) Klystron Global LLC
# All Rights Reserved
# https://www.klystronglobal.com/


{
    'name': 'Sales Profit',
    'summary': """
        Sales Profit """,
    'description': """
           Sales Profit.""",
    'author': 'Klystron Global',
    'maintainer': 'Bebisha C P',
    'website': "https://www.klystronglobal.com/",
    'category': 'sale',
    'version': '17.0.0.1',
    'license': 'AGPL-3',
    'depends': ['sale','purchase','web_approval'],
    'data': [
        # 'data/sale_profit.xml',
        # 'security/ir.model.access.csv',

        # 'views/sale_profit_views.xml',
        'views/purchase_order_views.xml',
        # 'data/sale_profit.xml',
    ],
}
