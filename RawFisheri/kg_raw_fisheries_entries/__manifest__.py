# -*- coding: utf-8 -*-
{
    'name': 'KG Raw Fisheries Entries',
    'version': '17.0',
    'summary': 'Raw Fisheries ERP',
    'description': 'Enterprise Odoo ERP Implementation for Raw Fisheries',
    'category': 'Other',
    'author': 'KG',
    'license': 'AGPL-3',
    'website': 'www.klystronglobal.com',
    'depends': ['base', 'hr', 'kg_raw_fisheries_hrms', 'kg_raw_fisheries_inventory', 'stock_account',
                'kg_raw_fisheries_sale', 'kg_raw_fisheries_purchase', 'stock'],
    'data': [
        'security/ir.model.access.csv',

        'data/ir_sequence.xml',

        'wizard/daily_catch_report_wizard_views.xml',
        'wizard/fuel_analysis_report_wizard_views.xml',
        'wizard/fuel_usage_analysis_report_wizard_views.xml',
        'wizard/production_report_wizard_views.xml',
        # 'wizard/menu.xml',

        'views/budget_activity_views.xml',
        'views/budget_usage_entry_views.xml',
        'views/daily_catch_views.xml',
        'views/fuel_analysis_views.xml',
        'views/fuel_usage_analysis_views.xml',
        'views/inventory_update_views.xml',
        'views/daily_stock_views.xml',
        'views/product_template_views.xml',
        'views/stock_move_lines_views.xml',
        'views/stock_move_views.xml',
        'views/stock_valuation_layer.xml',
        'views/stock_quant_views.xml',
        'views/menu.xml',

    ],
    # 'assets': {
    #     'web.assets_backend': [
    #         'kg_raw_fisheries_entries/static/src/xml/views/**/*',
    #         'kg_raw_fisheries_entries/static/src/js/**/*',
    #     ],
    # },
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,

}
