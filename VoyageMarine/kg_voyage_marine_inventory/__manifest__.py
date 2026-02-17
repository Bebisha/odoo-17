# -*- coding: utf-8 -*-
{
    'name': "KG Voyage Marine Inventory",

    "summary": "Customization for Inventory Module",
    "version": "17.0.1.0.0",
    'category': 'Inventory',
    'author': "Klystron Global",
    'maintainer': "SHARMI SV",
    "license": "OPL-1",
    'website': 'https://www.klystronglobal.com',
    'depends': ['base', 'stock', 'quality_control', 'mrp', 'product', 'mail', 'mrp_account', 'sale', 'stock_delivery',
                'purchase', 'industry_fsm_sale', 'account', 'stock_barcode'],
    'data': [
        'security/ir.model.access.csv',

        'data/product_group_data.xml',
        # 'data/product_category_data.xml',
        'data/cron.xml',
        'data/sequence.xml',
        'data/paper_format.xml',

        'report/delivery_note_report.xml',
        'report/delivery_order_report.xml',
        'report/report.xml',
        'report/picking_operations_report.xml',

        'views/stock_picking_views.xml',
        'views/sub_category_views.xml',
        'views/brand_views.xml',
        'views/product_category_views.xml',
        'views/product_views.xml',
        'views/product_part_number_views.xml',
        'views/product_group_views.xml',
        'views/physical_status_views.xml',
        'views/make_views.xml',
        'views/model_views.xml',
        'views/stock_location_views.xml',
        'views/stock_picking_type_views.xml',

        'wizard/dn_select_products.xml',
    ],

}
