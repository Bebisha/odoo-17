# -*- coding: utf-8 -*-

{
    'name': 'Finance Lease Management',
    'version': '17.1.1',
    'category': 'Accounting',
    'author': ' Bista Solutions Pvt. Ltd',
    'website': 'http://www.bistasolutions.com/',
    "license": "AGPL-3",
    'summary': "Manage Customer Loan",
    'description': """
       This module allow user to manage customer loan.
    """,
    'author': 'Bista Solutions Pvt. Ltd.',
    'website': 'https://www.bistasolutions.com',
    'depends': ['account'],
    'data': [
        'security/user_groups.xml',
        'security/ir.model.access.csv',
        'views/loan_sequence.xml',
        'wizard/account_loan_pay_amount_view.xml',
        'wizard/account_loan_pay_full_amount_view.xml',
        'views/account_loan_history_view.xml',
        'wizard/loan_report_print.xml',
        'views/loan_view.xml',
        'views/loan_action_view.xml',
        'views/loan_menu_view.xml',
        # 'views/templates.xml',
        'wizard/loan_reject_form_view.xml',
        'wizard/reschedule_wiz_view.xml',
        # 'report/report_register.xml',
        # 'report/loan_request_report.xml',
        # 'report/loan_report.xml',
        # 'report/loan_summary_report.xml',

    ],
    'demo': [],
    'images': [],
    'application': True,
    'installable': True,
    # 'auto_install': False,
    'external_dependencies': {
        'python': [
            'numpy',
        ], }
}
