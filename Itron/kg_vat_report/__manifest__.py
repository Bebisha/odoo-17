# -*- coding: utf-8 -*-
{
    'name': "kg_vat_report",

    'summary': """
        Get invoice details for receipts or payment made in a period.
        """,

    'description': """
        
    """,

    'author': "Pranav",
    'website': "http://www.klystronglobal.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['account'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/invoice_details_report_views.xml',
    ],
}
