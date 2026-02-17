# -*- coding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'Mail SMTP Server Per User',
    'summary': 'Send mails from Odoo using your own mail.',
    'author': 'Bista Solutions Inc',
    'website': 'https://www.bistasolutions.com/',

    'description': """
Mail SMTP Server Per User
=========================.
""",
    'version': '17.1.1',
    'license': 'LGPL-3',
    'category': 'Mail',
    'depends': ['google_gmail'],
    'data': [
            # 'security/ir.model.access.csv',
            'views/ir_mail_server_view.xml',
        ],
    'installable': True,
    'application': True,
    # 'auto_install': True
}
