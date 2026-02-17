# -*- coding: utf-8 -*-


{
    'name': 'KG Raw Fisheries Accounting',
    'version': '17.0',
    'summary': 'Raw Fisheries ERP',
    'description': 'Enterprise Odoo ERP Implementation for Raw Fisheries',
    'category': 'Other',
    'author': 'KG',
    'license': 'AGPL-3',
    'website': 'www.klystronglobal.com',
    'depends': ['base', 'account', 'sale', 'kg_raw_fisheries_sale', 'kg_raw_fisheries_approvals'],
    'data': [
        'security/ir.model.access.csv',

        'data/res_groups.xml',
        'data/sequence.xml',
        'data/paper_format.xml',
        'data/mail_template.xml',

        'reports/management_cost_views.xml',
        'reports/management_cost_monthly_views.xml',
        'reports/tax_invoice_report.xml',
        'reports/report.xml',

        'wizard/management_cost_wizard_views.xml',
        'wizard/management_cost_monthly_wizard_views.xml',
        'wizard/management_cost_split_wizard_views.xml',
        'wizard/reject_reason_wizard.xml',
        'wizard/forward_approval_wizard.xml',

        'views/account_move.xml',
        'views/budget_views.xml',
        'views/account_analytic_account_views.xml',
        'views/res_company_views.xml',
        'views/res_config_views.xml',
        'views/thank_you_template.xml',
        'views/res_users_views.xml',
        'views/invoice_bill_approvals.xml',
        'views/res_partner_bank_views.xml',
        'views/res_partner_views.xml',
        'views/account_analytic_line_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'kg_raw_fisheries_accounting/static/src/js/invoice_bill_approvals_dashboard.js',
            'kg_raw_fisheries_accounting/static/src/xml/invoice_bill_approvals_dashboard.xml',
        ],
    },

    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,

}
