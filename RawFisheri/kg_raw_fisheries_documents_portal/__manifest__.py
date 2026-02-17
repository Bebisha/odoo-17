# -*- coding: utf-8 -*-
{
    'name': "KG Raw Fisheries Documents Portal",

    "summary": "Customization for Documents Portal Module",
    "version": "17.0.1.0.0",
    'category': 'Documents Poratl',
    'author': "Klystron Global",
    'maintainer': "SHARMI SV",
    "license": "OPL-1",
    'website': 'https://www.klystronglobal.com',
    'depends': ['base', 'kg_raw_fisheries_documents', 'website', 'portal', 'mail'],
    'data': [
        'security/ir.model.access.csv',

        'data/website_menu.xml',
        'data/sequence.xml',
        'data/res_groups.xml',
        'data/ir_rule.xml',

        'views/add_customer_documents.xml',
        'views/customer_own_documents.xml',
        'views/thank_you_page_template.xml',
        'views/transaction_documents_views.xml',
        'views/transaction_documents_type_views.xml',
        'views/transaction_documents_portal_view.xml',

        'wizard/td_reject_reason_wizard.xml',


    ],
}
