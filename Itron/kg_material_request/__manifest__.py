# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Material Request',
    'version': '17.0.1.0.0',
    'category': '',
    'summary': '',
    'description': """Material Request""",
    'depends': ['base','sale', 'stock','product' ,'kg_timeoff_dashboard','account'],
    'data': [
        'security/ir.model.access.csv',
        'security/material_groups.xml',

        'data/mtr_sequence.xml',
        'views/material_request.xml',
        'views/res_settings.xml',
        'views/stock_picking.xml',
        'views/product.xml',
        'views/partner.xml',
        'views/purchase_order_view.xml',
        'views/dashboard_menu.xml',

        'report/purchase_report.xml',

        'wizard/reject_reason_wizard.xml',
        'wizard/update_quantity-wizard.xml',
        'wizard/reject_reason_receipt_view.xml',

    ],

    "assets": {
        "web.assets_backend": [
            'kg_material_request/static/src/js/material_request_dashboard.js',
            'kg_material_request/static/src/xml/material_request_dashboard_template.xml',

            'kg_material_request/static/src/xml/inventroy_valuation_dashboard.xml',
            'kg_material_request/static/src/js/inventory_valuation_dashboard.js',

        ]

    },

    'sequence': -1,
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
