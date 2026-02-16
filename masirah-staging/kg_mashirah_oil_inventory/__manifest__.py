# -*- coding: utf-8 -*-
{
    'name': "KG Mashirah Oil Inventory",

    "summary": "Customization for Inventory Module",
    "version": "17.0.1.0.0",
    'category': 'Inventory',
    'author': "Klystron Global",
    'maintainer': "SHARMI SV",
    "license": "OPL-1",
    'website': 'https://www.klystronglobal.com',
    # any module necessary for this one to work correctly
    'depends': ['base', 'stock', 'product', 'kg_mashirah_oil_accounting', 'sale', 'uom', 'account'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',

        'data/server_action.xml',
        'data/sequence.xml',
        'data/cron.xml',
        'data/activity.xml',

        'views/product_category_views.xml',
        'views/product_template_views.xml',
        'views/product_product_views.xml',
        'views/product_supplier_info.xml',
        'views/stock_move_views.xml',
        'views/material_consumption.xml',
        'views/res_config_settings_views.xml',
        'views/stock_scrap_views.xml',

        'report/print_labels_report.xml',

        'wizard/stock_report_wizard.xml'
    ],

}
