# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': "TDCC Sales Commission",
    'version': '17.1.1',
    'license': 'LGPL-3',
    'depends': ['bista_tdcc_operations', 'l10n_tdcc_coa'],
    'author': "Bista Solutions",
    'website': "http://www.bistasolutions.com",
    'category': "TDCC",
    'summary': "Manage Sales Commission",
    'description': """
    """,
    'data': [
            'security/commission_security.xml',
            'security/ir.model.access.csv',
            'data/commission_data.xml',
            'data/generate_commision_cron.xml',
            'views/sale_commission_views.xml',
            'wizard/sale_commission_wizard_view.xml',
            'views/res_config_settings_views.xml',
            'views/res_users_views.xml',
            'views/receipt_commission_view.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
    # 'auto_install': False
}
