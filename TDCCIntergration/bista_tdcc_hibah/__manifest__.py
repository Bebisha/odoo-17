# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': "Hibah Fund Management",
    'version': '17.1.1',
    'license': 'LGPL-3',
    'depends': [
        'bista_tdcc_operations',
        'account_asset',
        'bista_payment_term',
    ],
    'author': "Bista Solutions",
    'website': "http://www.bistasolutions.com",
    'category': "TDCC",
    'summary': """
        Manage Hibah Funds
    """,
    'description': """
    """,
    'data': [
        'security/ir.model.access.csv',
        'views/partner_view.xml',
        'wizard/sponsor_payment_details_wizard_view.xml',
        'wizard/statement_of_account_report.xml',
        'report/report_sponsor_payment_template.xml',
        'report/sponsor_payment_report.xml',
        'report/statement_report_template.xml',
        'views/account_payment_view.xml',
        'views/account_invoice_view.xml',
        'wizard/sponsor_details.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
    # 'auto_install': False
}
