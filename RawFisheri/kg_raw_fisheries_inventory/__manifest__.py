# -*- coding: utf-8 -*-
{
    'name': 'KG Raw Fisheries Inentory',
    'version': '17.0',
    'summary': 'Raw Fisheries ERP',
    'description': 'Enterprise Odoo ERP Implementation for Raw Fisheries',
    'category': 'Other',
    'author': 'KG',
    'license': 'AGPL-3',
    'website': 'www.klystronglobal.com',
    'depends': ['base', 'stock', 'kg_raw_fisheries_hrms', 'stock_account', 'spreadsheet_dashboard_stock_account',
                'spreadsheet_dashboard_stock'],
    'data': [
        'data/ir_rule.xml',
        "data/dashboards.xml",

        'views/res_users_views.xml',
        'views/stock_valuation_layer.xml',
        'views/stock_warehouse_views.xml',
        'views/stock_move_line_views.xml',
        'views/stock_move_views.xml',
        'views/stock_quant_views.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,

}
