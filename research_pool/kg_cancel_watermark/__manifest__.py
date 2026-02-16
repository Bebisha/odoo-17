# -*- coding: utf-8 -*-

# Klystron Global LLC
# Copyright (C) Klystron Global LLC
# All Rights Reserved
# https://www.klystronglobal.com/
{
    'name': 'Watermark for Sale / Purchase / Invoice / Bill',
    'category': '',
    'sequence': 10,
    'website': '',
    'summary': 'Watermark for Sale / Purchase / Invoice / Bill in cancel and draft state',
    'version': '17.0.0.1',
    'author': 'Klystron Global',
    'maintainer':'Binu A R',
    'website': "https://www.klystronglobal.com/",
    'description': """
        Watermark for Sale / Purchase / Invoice / Bill in cancel and draft state
        """,
    'depends': ['base', 'sale', 'sale_management', 'purchase', 'account'],

    'data': [
        'view/sale_order_report.xml',
        'view/invoice_report.xml',
        'report/purchase_order_report.xml'
    ],
    'installable': True,
    'license': 'AGPL-3',
}
