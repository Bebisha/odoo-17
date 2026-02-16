# -*- encoding: utf-8 -*-
#
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
#
{
    'name': "TDCC Account Reports",

    'summary': """
       TDCC Account Report""",

    'description': """
         TDCC Account Report
    """,

    'author': "Bista Solutions",
    'website': "http://www.bistasolutions.com",

    'category': 'Report',
    'version': '17.1.1',
    'license': 'LGPL-3',

    'depends': ['bista_tdcc_operations', 'bista_account_pdc',],

    'data': [
        'security/ir.model.access.csv',
        'report/receipt_by_payment_method_template.xml',
        'report/annual_invoice_report_template.xml',
        'report/account_move_report_template.xml',
        'report/account_reports.xml',
        'wizard/account_report_wizard.xml',
        'wizard/tax_report_wizard.xml',
        'wizard/cashflow_report.xml',
        # 'views/account_report_views.xml',
        'views/account_invoice_view.xml',
        'report/tax_report_pdf.xml',
        'report/receipt_by_payment_method_summary.xml',
        'report/receipt_by_payment_method_je.xml',
        'report/sales_by_practitioner_detail.xml',
        'report/sales_by_practitioner_summary.xml',
        'report/appointment_by_practitioner.xml',
        'report/allocation_by_practitioner.xml',
        'report/sales_by_service_type.xml',
        'report/sales_by_service_type_summary.xml',

    ],
    'installable': True,
    'application': True,
    # 'auto_install': False
}
