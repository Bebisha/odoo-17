# -*- coding: utf-8 -*-

# Klystron Global LLC
# Copyright (C) Klystron Global LLC
# All Rights Reserved
{
    'name': 'Custom Purchase',
    'summary': """
        Custom Purchase module""",
    'description': """
         Custom Purchase module""",
    'author': 'Klystron Global',
    'maintainer': 'Bebisha C P',
    'website': "https://www.klystronglobal.com/",
    'category': 'Purchase',
    'version': '17.0.0.1',
    'license': 'AGPL-3',
    'depends': ['purchase', 'base', 'sale', 'stock', 'account', 'kg_voyage_marine_crm', 'project','purchase_requisition',
                'purchase_product_matrix', 'kg_voyage_marine_inventory', 'material_purchase_requisition'],
    'data': [
        'security/ir.model.access.csv',
        'security/groups.xml',

        'data/activity.xml',
        'data/sequence.xml',
        'wizard/purchase_order_wizard_view.xml',
        'wizard/stock_picking_return_views.xml',
        'wizard/direct_po_from_so.xml',
        'views/purchase_order_views.xml',
        'views/res_config_settings_views.xml',
        'views/sale_order_views.xml',
        'views/reports.xml',
        'views/purchase_terms_conditions.xml',
        'views/res_partner_views.xml',
        'views/portal_templates.xml',
        'views/account_move_views.xml',
        'views/vendor_group_views.xml',
        'report/purchase_order_template.xml',
        'report/rfq_template.xml',
        'report/purchase_order_report.xml',
        'report/purchase_report_views.xml',

    ],


}
