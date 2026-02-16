# -*- coding: utf-8 -*-

# Klystron Global LLC
# Copyright (C) Klystron Global LLC
# All Rights Reserved
# https://www.klystronglobal.com/


{
    'name': "Product Pack",
    'summary': """
          Product Pack""",
    'description': """
             Product Pack in sale order""",
    'author': 'Klystron Global',
    'maintainer':'Bebisha C P',
    'website': "https://www.klystronglobal.com/",
     'category': 'Sales',
    'version': '17.0.0.1',
    'license': 'LGPL-3',
    'depends': ['sale_management','account_accountant'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_view.xml',
        'views/sale_view.xml',
        'wizard/product_wizard_view.xml'

    ],

}


