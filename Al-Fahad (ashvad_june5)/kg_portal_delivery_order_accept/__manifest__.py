# -*- coding: utf-8 -*-

# Klystron Global LLC
# Copyright (C) Klystron Global LLC
# All Rights Reserved
# https://www.klystronglobal.com/


{
    'name': 'Portal Delivery Order Accepted Invoice ',
    'summary': """
         Portal Delivery Order Accepted Invoice """,
    'description': """
            Portal Delivery Order Accepted Invoice """,
    'author': 'Klystron Global',
    'maintainer':'Bebisha C P',
    'website': "https://www.klystronglobal.com/",
     'category': 'Inventory',
    'version': '17.0.0.1',
    'license': 'AGPL-3',
    'depends': ['base', 'stock','barcodes','website_sale','portal','account'],
    'data': [
        'security/ir.model.access.csv',
        'views/portal_template_views.xml',
        'views/invoice_email_template.xml',
        # 'views/website_sale_template_views.xml',
    #

    ],

}
