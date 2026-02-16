# -*- coding: utf-8 -*-

# Klystron Global LLC
# Copyright (C) Klystron Global LLC
# All Rights Reserved
{
    'name': 'Cash Book Report',
    'summary': """
        Generates cash book report in both Excel and PDF formats.""",
    'description': """
         Generates cash book report in both Excel and PDF formats.""",
    'author': 'Klystron Global',
    'maintainer': 'Bebisha C P',
    'website': "https://www.klystronglobal.com/",
    'category': 'Acounting',
    'version': '17.0.0.1',
    'license': 'AGPL-3',
    'depends': ['account_accountant', 'base'],
    'data': [

        'security/ir.model.access.csv',
'wizard/cashbook.xml',
        'report/cashbook_pfd_report.xml',

        'report/report_cashbook.xml',


    ],
}



