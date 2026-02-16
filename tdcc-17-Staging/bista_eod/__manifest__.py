# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': "TDCC End of Day Process",
    'summary': """
        TDCC End of Day Process""",
    'description': """
        TDCC End of Day Process
    """,
    'author': "Bista Solutions",
    'website': "http://www.bistasolutions.com",
    'category': 'TDCC',
    'version': '17.1.1',
    'license': 'LGPL-3',
    'depends': ['bista_tdcc_operations', 'bista_account_pdc',],
    'data': [
        'security/ir.model.access.csv',
        'data/eod_data.xml',
        'views/end_of_day_views.xml',
    ],
    'installable': True,
    # 'auto_install': False,

}
