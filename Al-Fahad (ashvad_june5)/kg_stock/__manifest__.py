# -*- coding: utf-8 -*-
{
    'name': "Warehouse user restriction",

    "summary": "Warehouse user restriction",
    "version": "17.0.1.0.0",
    'category': 'sale',
    'author': "Klystron Global",
    "license": "OPL-1",
    'depends': ['base', 'sale', 'mail','stock','product','website','website_sale','portal'],
    'data': [
        'security/security.xml',
        # 'data/mail_template.xml',
        # 'views/product_listing_template.xml',
        'views/product_view.xml',
    ]
}
