# -*- encoding: utf-8 -*-
#
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
#
{
    'name': "Bista Product Pack",

    'summary': """
       Bista Product Pack""",

    'description': """
       Bista Product Pack
    """,

    'author': "Bista Solutions",
    'website': "http://www.bistasolutions.com",

    'category': 'Sales',
    'version': '17.1.1',
    'license': 'LGPL-3',

    'depends': ['sale_management','account',],

    'data': [
        'security/ir.model.access.csv',
        'views/product_view.xml',
        'views/sale_view.xml',
        'wizard/product_wizard_view.xml',
        'wizard/invoice_product_pack_views.xml'
    ],
    'installable': True,
    'application': True,
    # 'auto_install': False
}
