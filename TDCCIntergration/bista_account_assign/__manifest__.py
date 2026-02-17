# -*- encoding: utf-8 -*-
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
#

{
    'name': 'Bista Assets Management',
    'version': '17.1.1',
    'category': 'Accounting',
    'description': """
Bista Assets management
========================
    * Manage assets of company or a person.
    """,
    'author': 'Bista Solutions Pvt. Ltd.',
    'website': 'http://www.bistasolutions.com',
    'depends': ['account_asset', 'bista_hr',],
    'data': [
        "security/asset_security.xml",
        "security/ir.model.access.csv",
        'views/account_asset_view.xml',
        "wizard/account_assign_wiz_view.xml",
    ],
    'installable': True,
    'auto-install': True,
    'license': 'LGPL-3',
    'module_type': 'official',
}
