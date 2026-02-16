# -*- coding: utf-8 -*-
#
{
    'name': 'UAE Check Printing',
    'version': '17.1.1',
    'category': 'Localization',
    'summary': 'Print UAE Checks',
    'description': """
    This module allows to print your payments on pre-printed check paper.
     """,
    'author': 'Bista Solutions',
    'company': 'Bista Solutions',
    'category': 'Accounting',
    'depends': [
        'account', 'account_payment',
        'account_check_printing',
        'l10n_us_check_printing',
        'bista_account_pdc'
    ],
    'license': 'LGPL-3',
    'data': [
        'security/ir.model.access.csv',
        'data/report.xml',
        # 'data/nbd_bank_check_print_demo_data.xml',
        'report/print_check.xml',
        'views/check_format_view.xml',
        'wizard/print_prenumbered_checks_views.xml',
        'views/account_checkbook_view.xml',
        'views/account_journal_view.xml',
    ],
    'demo': [],
    'images': [],
    'installable': True,
    'auto_install': False,
    # 'application': True,
}
