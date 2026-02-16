# -*- coding: utf-8 -*-

# Klystron Global LLC
# Copyright (C) Klystron Global LLC
# All Rights Reserved
# https://www.klystronglobal.com/


{
    'name': 'SalesPerson Weekly Report',
    'summary': """Weekly and Monthly Report on Salesperson using Email Template""",
    'description': """
           To generate a weekly and monthly report on salespersons using an Odoo template.""",
    'author': 'Klystron Global',
    'maintainer': 'Bebisha C P',
    'website': "https://www.klystronglobal.com/",
    'category': 'sale',
    'version': '17.0.0.1',
    'license': 'AGPL-3',
    'depends': ['sale', 'mail','base'],
    'data': [
        'data/ir_cron.xml',
        'report/weekly_report.xml',
        'report/monthly_report.xml',
        'views/configuration_views.xml',
    ],
}
