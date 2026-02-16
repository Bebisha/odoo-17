# -*- coding: utf-8 -*-
{
    'name': "AL Sharqiya Accounting",

    "summary": "Customization for Accounting Module",
    "version": "17.0.1.0.0",
    'category': 'Accounting',
    'author': "Klystron Global",
    'maintainer': "SHARMI SV",
    "license": "OPL-1",
    'website': 'https://www.klystronglobal.com',
    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'account_asset', 'account_reports', 'account_budget',
                'account_accountant',
                'account_followup'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',

        'report/account_general_report.xml',
        'report/trial_balance_template.xml',
        'report/report.xml',

        'views/account_tag_view.xml',
        'wizard/account_general_report_wizard.xml',
        'wizard/account_trial_balance_report.xml',
    ],

}
