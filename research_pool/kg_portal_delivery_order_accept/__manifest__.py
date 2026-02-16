# -*- coding: utf-8 -*-

# Klystron Global LLC
# Copyright (C) Klystron Global LLC
# All Rights Reserved
# https://www.klystronglobal.com/


{
    'name': 'Portal Delivery Order Accepted Invoice ',
    'summary': """
         Portal Delivery Order Accepted Invoice """,
    'description': """
            Portal Delivery Order Accepted Invoice """,
    'author': 'Klystron Global',
    'maintainer':'Bebisha C P',
    'website': "https://www.klystronglobal.com/",
     'category': 'Inventory',
    'version': '17.0.0.1',
    'license': 'AGPL-3',
    'depends': ['base', 'stock','web'],
    'data': [
        'security/ir.model.access.csv',
        'views/portal_template_views.xml',

    ],
    # 'assets': {
    #     'web.assets_backend': [
    #
    #         'kg_portal_delivery_order_accept/static/src/js/popup.js',
    #     ]
    # }
}
