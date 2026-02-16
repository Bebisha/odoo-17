# -*- coding: utf-8 -*-

# Klystron Global LLC
# Copyright (C) Klystron Global LLC
# All Rights Reserved
# https://www.klystronglobal.com/


{
    'name': 'Auto Create Delivery Order from Invoice',
    'summary': """
        To automatically create a delivery order from an invoice""",
    'description': """
          Auto Create Delivery Order from Invoice""",
    'author': 'Klystron Global',
    'maintainer':'Bebisha C P',
    'website': "https://www.klystronglobal.com/",
    'category': 'Invoice',
    'version': '17.0.0.1',
    'license': 'AGPL-3',
    'depends': ['account_accountant','stock_account'],
    'data': [
        'views/invoice_views.xml',
    ],
}
