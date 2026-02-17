# -*- encoding: utf-8 -*-
#
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
#
{
    'name': 'Payment Terms',
    'version': '17.1.1',
    'license': 'LGPL-3',
    'summary': 'Payment Term Extensions',
    'description': """
    Add Invoice amount breakup on Invoice level.
    """,
    'category': 'Invoicing Management',
    'website': 'http://www.bistasolutions.com',
    'data': ['security/ir.model.access.csv',
             'views/account_invoice_view.xml'],
    'depends': ['account'],
    'installable': True,
    'application': True,
    # 'auto_install': False,
}
