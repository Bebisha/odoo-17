# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': "Intensive Program Operations",

    'summary': """
        Intensive Program Operations""",

    'description': """
        Intensive Program Operations
    """,

    'author': "Bista Solutions",
    'website': "http://www.bistasolutions.com",

    'category': 'TDCC',
    'version': '17.1.1',
    'license': 'LGPL-3',

    'depends': ['bista_tdcc_operations'],

    'data': [
        'security/ir.model.access.csv',
        'views/eiip_group_views.xml',
        'views/crm_view.xml',
        'views/sale_view.xml',
    ],
    'installable': True,
    # 'auto_install': False,
    'application': True,
}
