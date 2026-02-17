# -*- coding: utf-8 -*-
# Copyright 2015 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Sale Advance Payment",
    "version": "17.0.1.0.0",
    "author": "Comunitea",
    'website': 'www.counitea.com',
    "category": "Sales",
    "description": """Allow to add advance payments on sales and then use its
 on invoices""",
    "depends": ["base", "sale", "account","purchase"],
    "data": ["wizard/sale_advance_payment_wzd_view.xml",
             'wizard/purchase_advance_payment_wzd.xml',
             "views/sale_view.xml",
             'views/purchase.xml',
             "report/sale_advance_report.xml",
             "report/sale_advance_report_template.xml",
             'report/purchase_advance_report.xml',
             'report/purchase_advance_report_template.xml',
             "security/ir.model.access.csv"],
    "installable": True,
}
