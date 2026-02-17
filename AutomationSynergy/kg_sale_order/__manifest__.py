# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-

# Klystron Global LLC
# Copyright (C) Klystron Global LLC
# All Rights Reserved
# https://www.klystronglobal.com/


{
    'name': "KG Sale",
    'summary': """
         sale""",
    'description': """
            Sale""",
    'author': 'Klystron Global',
    'maintainer': 'Bebisha C P',
    'website': "https://www.klystronglobal.com/",
    'category': 'Sale',
    'version': '17.0.0.1',
    'license': 'LGPL-3',
    'depends': ['base', 'sale', 'sale_project', 'kg_project', 'project', 'stranbys_saleorder_revision'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_number.xml',
        'data/customer_type.xml',
        'reports/sale_quotation_template.xml',
        'views/sale_order_views.xml',
        'views/project_views.xml',
        'views/delivery_note_template.xml',
        'views/res_company_views.xml',
        'views/res_partner_views.xml',
        'views/customer_type_views.xml',
        'views/sale_terms_and_conditions_view.xml',
        'wizard/sale_order_confirm_wizard_views.xml',


    ],

}