# -*- coding: utf-8 -*-
{
    'name': "KG Mashirah Oil Accounting",

    "summary": "Customization for Accounting and Invoicing Module",
    "version": "17.0.1.0.0",
    'category': 'Accounting, Invoicing',
    'author': "Klystron Global",
    'maintainer': "SHARMI SV",
    "license": "OPL-1",
    'website': 'https://www.klystronglobal.com',
    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'sale', 'kg_mashirah_oil_purchase'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/activity.xml',
        'data/paper_format.xml',
        'views/account_move_views.xml',
        'views/account_payment_views.xml',
        'views/account_tax_views.xml',

        'report/debit_note_report.xml',
        'report/payment_voucher_report.xml',
        'report/journal_voucher_report.xml',
        'report/day_book_report.xml',
        'report/report.xml',

        'wizard/day_book_report_wizard.xml',
        'wizard/vat_return_report_views.xml',
        'wizard/checklist_wizard.xml'
    ],

}
