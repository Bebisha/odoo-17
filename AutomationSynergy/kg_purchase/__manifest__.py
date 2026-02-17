# -*- coding: utf-8 -*-

# Klystron Global LLC
# Copyright (C) Klystron Global LLC
# All Rights Reserved
# https://www.klystronglobal.com/


{
    'name': "KG Purchase",
    'summary': """
        KG Purchase""",
    'description': """
             KG Purchase""",
    'author': 'Klystron Global',
    'maintainer': 'Bebisha C P',
    'website': "https://www.klystronglobal.com/",
    'category': 'Purchase',
    'version': '17.0.0.1',
    'license': 'LGPL-3',
    'depends': ['base', 'stock', 'purchase', 'purchase_stock','kg_accounting','kg_gnr'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_number.xml',
        'data/vendor_type.xml',
        'data/user.xml',
        'reports/purchase_order_report.xml',
        'reports/purchase_order_printout_template.xml',
        'views/res_partner_views.xml',
        'views/po_term_print.xml',
        'views/vendor_puirchase_report.xml',
        'views/purchase_views.xml',
        'views/custom_terms_conditions_views.xml',
        'views/stock_picking_views.xml',
        'views/vendor_type_views.xml',

    ],

}
