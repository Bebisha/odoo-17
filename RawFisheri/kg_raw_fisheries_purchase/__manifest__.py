# -*- coding: utf-8 -*-
{
    'name': "KG Raw Fisheries Purchase",

    "summary": "Customization for Purchase Module",
    "version": "17.0.1.0.0",
    'category': 'Purchase',
    'author': "Klystron Global",
    'maintainer': "SHARMI SV",
    "license": "OPL-1",
    'website': 'https://www.klystronglobal.com',
    'depends': ['base', 'purchase', 'kg_raw_fisheries_hrms', 'mail', 'account'],
    'data': [
        'security/ir.model.access.csv',

        'data/sequence.xml',
        'data/server_action.xml',
        'data/paper_format.xml',

        'views/purchase_order_views.xml',
        'views/purchase_enquiry_views.xml',
        'views/purchase_enquiry_type_views.xml',
        'views/purchase_entry_views.xml',
        'views/purchase_entry_template.xml',

        'wizard/import_pol_wizard_views.xml',
        'wizard/import_po_enquiry_wizard.xml',
        'wizard/reject_reason_wizard.xml',

        'report/purchase_order_report.xml',
        'report/report.xml',
    ],
}
