# -*- coding: utf-8 -*-
{
    "name": "KG Currency Conversion",
    "summary": "Currency Conversion",
    'version': '17.0.0.0',
    "category": "sale",
    "website": "www.klystronglobal.com",
    "description": """
        Currency Conversion
    """,

    "author": "Ameen",
    "installable": True,
    "depends": [
        'sale', 'account', 'purchase','project'
    ],
    "data": [
        'security/ir.model.access.csv',
        'wizard/invoice_wizard.xml',
        'wizard/po_wizard.xml',
        'wizard/so_wizard.xml',
        'wizard/sale_make_invoice_view.xml',
        'views/kg_sale_view.xml',
        'views/kg_po_view.xml',
        'views/kg_invoice_view.xml',
        'views/company_view.xml',
        'views/kg_tax_view.xml',
        # 'views/kg_industry.xml',
        'views/journal_voucher_view.xml',
        'report/kg_po_with_logo.xml',
        'report/reports.xml',
        'report/kg_llc_inv.xml',
        'report/kg_invoice_with_header.xml',
        'report/kg_so_with_logo.xml',
    ],
}
