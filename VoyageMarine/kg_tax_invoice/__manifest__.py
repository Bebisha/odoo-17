# -*- coding: utf-8 -*-

# Klystron Global LLC
# Copyright (C) Klystron Global LLC
# All Rights Reserved
# https://www.klystronglobal.com/

{
    'name': 'Tax Invoice',
    'version': '17.0.1.0.0',
    'license': 'LGPL-3',
    'depends': ['base', 'account_accountant', 'account', 'kg_voyage_marine_accounting', 'mail'],
    'sequence': '-100',
    'category': '',
    'author': 'Klystron Global',
    'maintainer': 'Klystron Global',
    'website': "www.klystronglobal.com",
    'application': True,
    'description': """The Module provide custom tax invoice""",
    'data': [
        'security/ir.model.access.csv',

        'views/report.xml',
        'views/invoice_attchment_master_views.xml',
        'views/account_move_views.xml',

        'report/tax_invoice.xml',

    ],

    "installable": True,
    'demo': [],

}
