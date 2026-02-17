# -*- coding: utf-8 -*-

{
    'name': 'Advance Payment Allocation ',
    'version': '17.0.1.0.0',
    'license': 'LGPL-3',
    'category': 'Accounting',
    "sequence": 1,
    'summary': 'Managing Payments and Reconcilation ',
    'complexity': "easy",
    'author': 'Klystron Global',
    'price':10.00,
    'currency':'USD',
    "license": "AGPL-3",
    'depends': ['base', 'account',],
    'data': [

        'security/ir.model.access.csv',
        'data/sequance.xml',
        'views/inherit_invoice.xml',
        'views/journal_vocher.xml',
        'wizard/payment_allocation_wizard.xml',

    ],
    'images':  ['static/description/logo.png'],


    'demo': [

    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
