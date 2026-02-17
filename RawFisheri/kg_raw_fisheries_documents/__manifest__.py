# -*- coding: utf-8 -*-
{
    'name': "KG Raw Fisheries Documents",

    "summary": "Customization for Documents Module",
    "version": "17.0.1.0.0",
    'category': 'Documents',
    'author': "Klystron Global",
    'maintainer': "SHARMI SV",
    "license": "OPL-1",
    'website': 'https://www.klystronglobal.com',
    'depends': ['base', 'documents', 'kg_document_expiry', 'web', 'kg_raw_fisheries_hrms'],
    'data': [
        'security/ir.model.access.csv',

        'data/ir_rule.xml',

        'views/document_tags_views.xml',
        'views/documents_folder_views.xml',
        'views/documents_document.xml',
        'views/document_type_views.xml',
        'views/document_department_views.xml',
        'views/document_company_views.xml',
        'views/res_groups_views.xml',

        'wizard/documents_access_wizard.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'kg_raw_fisheries_documents/static/src/views/**/*',
        ]
    },

}
