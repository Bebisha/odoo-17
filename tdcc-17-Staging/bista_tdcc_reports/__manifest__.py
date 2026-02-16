# -*- encoding: utf-8 -*-
#
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
#
{
    'name': "TDCC Reports",
    'summary': """
        TDCC Reports""",
    'description': """
       TDCC Reports
    """,
    'author': "Bista Solutions",
    'website': "http://www.bistasolutions.com",
    'category': 'Report',
    'version': '17.1.1',
    'license': 'LGPL-3',
    'depends': ['bista_tdcc_operations'],
    'data': [
        'reports/quotation_report.xml',
        'reports/receipt_report.xml',
        'reports/invoice_report.xml',
        'reports/vendor_payment_report.xml',
        'reports/email_report.xml',
        'reports/report_register.xml',
        'reports/invoice_list_view_report.xml',
        'reports/payment_list_view_report.xml',
    ],
    'installable': True,
    'application': True,
    # 'auto_install': False

}
