# -*- coding: utf-8 -*-
{
    'name': "KG Mashirah Oil Purchase",

    "summary": "Customization for Purchase Module",
    "version": "17.0.1.0.0",
    'category': 'Purchase',
    'author': "Klystron Global",
    'maintainer': "SHARMI SV",
    "license": "OPL-1",
    'website': 'https://www.klystronglobal.com',
    # any module necessary for this one to work correctly
    'depends': ['base', 'purchase', 'stock', 'product', 'purchase_stock'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/access_rights.xml',
        'data/sequence.xml',
        'data/activity.xml',
        'data/activity_contract.xml',

        'views/res_company_views.xml',
        'views/purchase_order_views.xml',
        'views/purchase_contract_agreement_views.xml',
        'views/res_config_settings_views.xml',

        'report/request_for_quotation_template.xml',
        'report/purchase_order_template.xml',
        'report/report.xml',

        'wizard/purchase_contract_extend_wizard.xml',
    ],

}
