# -*- coding: utf-8 -*-
{
    'name': "KG Voyage Marine Accounting",

    "summary": "Customization for Accounting Module",
    "version": "17.0.1.0.0",
    'category': 'Accounting',
    'author': "Klystron Global",
    'maintainer': "SHARMI SV",
    "license": "OPL-1",
    'website': 'https://www.klystronglobal.com',
    'depends': ['base', 'account', 'kg_voyage_marine_sale','kg_voyage_marine_crm','account_reports', 'l10n_ae_corporate_tax_report'],
    'data': [
        'security/ir.model.access.csv',

        'data/partner_ledger.xml',
        'data/general_ledger.xml',
        'data/paper_format.xml',
        'data/sequence.xml',
        'data/corporate_tax_report.xml',

        'report/credit_note_report.xml',
        'report/debit_note_report.xml',
        'report/statement_account_report.xml',
        'report/report.xml',
        'report/account_report_views.xml',

        'wizard/statement_account_report_wizard.xml',
        'wizard/multi_expenses_wizard.xml',
        'wizard/attachment_validation_wizard.xml',

        'views/account_move_views.xml',
        'views/hr_expense_views.xml',
        'views/sale_views.xml',
    ],

}
