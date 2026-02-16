# -*- coding: utf-8 -*-

# Klystron Global LLC
# Copyright (C) Klystron Global LLC
# All Rights Reserved
# https://www.klystronglobal.com/


{
    'name': 'Stock Move Report',
    'summary': """Weekly and Monthly Report on roducts using Email Template""",
    'description': """
           To generate a weekly and monthly report on prodct move .""",
    'author': 'Klystron Global',
    'maintainer': 'Bebisha C P',
    'website': "https://www.klystronglobal.com/",
    'category': 'Stock',
    'version': '17.0.0.1',
    'license': 'AGPL-3',
    'depends': ['stock', 'mail','base'],
    'data': [
        'data/ir_cron.xml',
        'reports/weekly_stock_move.xml',
        'reports/monthly_stock_move_report.xml',
        'views/conf_setting_views.xml',
    ],
}
