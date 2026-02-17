# -*- coding: utf-8 -*-

{
    'name': 'KG Raw Fisheries Sales',
    'version': '17.0',
    'summary': 'Raw Fisheries ERP',
    'description': 'Enterprise Odoo ERP Implementation for Raw Fisheries',
    'category': 'Other',
    'author': 'KG',
    'license': 'AGPL-3',
    'website': 'www.klystronglobal.com',
    'depends': ['base', 'sale', 'kg_raw_fisheries_hrms', 'mail', 'sale_pdf_quote_builder'],
    'data': [
        'security/ir.model.access.csv',

        'data/paper_format.xml',
        'data/mail_template.xml',

        'reports/sale_price_history_report.xml',
        'reports/proforma_invoice_report.xml',
        'reports/sale_order_report.xml',
        'reports/report.xml',

        'views/sale_order_views.xml',
        'views/account_move_line_views.xml',
        'views/product_views.xml',
        'views/delivery_terms_views.xml',
        'views/stock_batch_views.xml',
        'views/so_customer_view_portal.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,

}
