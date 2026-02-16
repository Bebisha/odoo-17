# -*- coding: utf-8 -*-
{
    'name': "KG Portfolio Management",
    "summary": "Managing Investment,Stock Marketing",
    "version": "17.0.1.0.0",
    'category': 'Purchase, Sale',
    'author': "Klystron Global",
    "license": "OPL-1",
    'website': 'https://www.klystronglobal.com',
    # any module necessary for this one to work correctly
    'depends': ['base', 'account','account_accountant', 'sale', 'purchase'],
    # always loaded
    'data': [
        'data/sequence.xml',
        'data/journal_data.xml',
        'data/cron.xml',
        'security/ir.model.access.csv',
        'security/record_rule.xml',
        'security/investment_security.xml',
        'reports/purchase_report.xml',
        'reports/sale_report.xml',
        'reports/portfolio_report.xml',
        'reports/company_wise_report.xml',

        'views/investment_view.xml',
        'views/kg_purchase_view.xml',
        'views/kg_sale_view.xml',
        'views/dividend_entry_view.xml',
        'views/market_rate_view.xml',
        'views/revaluation_journal_view.xml',
        'views/kg_bond_view.xml',
        'views/kg_stock_quant_view.xml',
        'views/res_config_setting_view.xml',
        'views/investment_menus.xml',
        'wizards/purchase_summary_wizard.xml',
        'wizards/sale_summary_wizard.xml',
        'wizards/portfolio_summary_wizard.xml',
        'wizards/company_wise_report.xml',
        'wizards/bond_report_wizard.xml',

    ],

}
