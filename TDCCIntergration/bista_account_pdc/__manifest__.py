# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'Bista PDC Management',
    'version': '17.0.0.1',
    'author': 'Bista Solutions',
    'website': 'http://www.bistasolutions.com',
    'category': 'Accounting',
    'summary': 'Extension on Cheques to handle Post Dated Cheques',
    'description': """ Extension on Cheques to handle Post Dated Cheques """,
    'depends': ['account_check_printing', 'account',],
    'data': [
        'security/ir.model.access.csv',
        'data/pdc_scheduler.xml',
        'data/account_pdc_data.xml',
        'views/account_payment_view.xml',
        'views/res_config_view.xml',
        'wizard/pdc_payment_wiz_view.xml',
    ],
    'installable': True,
    # 'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}
