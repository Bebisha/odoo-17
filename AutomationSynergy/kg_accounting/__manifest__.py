# -*- coding: utf-8 -*-

# Klystron Global LLC
# Copyright (C) Klystron Global LLC
# All Rights Reserved
# https://www.klystronglobal.com/


{
    'name': "KG Accounting",
    'summary': """
        KG Accounting""",
    'description': """
             KG Accounting""",
    'author': 'Klystron Global',
    'maintainer': 'Bebisha C P',
    'website': "https://www.klystronglobal.com/",
    'category': 'Purchase',
    'version': '17.0.0.1',
    'license': 'LGPL-3',
    'depends': ['base', 'purchase', 'account_accountant', 'account', 'sign', 'sale'],
    'data': [
        'report/report.xml',
        'report/credit_note.xml',
        'report/invoice_report.xml',

        'views/res_partner_views.xml',
        'views/res_company.xml',
        'views/sale_order_views.xml',
        'views/res_partner_bank_views.xml',


    ],
}
