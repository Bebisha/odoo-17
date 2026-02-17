# -*- coding: utf-8 -*-
{
    'name': "Product/Material Purchase Requisitions by Employees/Users in odoo",

    "summary": "Material Purchase Requisition",
    "version": "17.0.1.0.0",
    'category': 'Purchase',
    'author': "Klystron Global",
    'maintainer': "SHARMI SV",
    "license": "OPL-1",
    'website': 'https://www.klystronglobal.com',
    # any module necessary for this one to work correctly
    'depends': ['sale_management', 'purchase', 'operating_unit', 'stock', 'hr', 'sale_stock', 'purchase_stock',
                'hr_payroll', 'quality', 'base', 'kg_voyage_marine_inventory','purchase_location_by_line', 'kg_voyage_marine_crm'],
    # always loaded
    'data': [
        'security/purchase_requisition_security.xml',
        'security/ir.model.access.csv',
        'data/picking_type.xml',
        'data/budget_exceed_email_template.xml',
        'data/activity.xml',

        'edi/purchase_requisition_template_view.xml',

        'report/material_requisition_report.xml',
        'report/material_requisition_report_view.xml',
        'report/purchase_requisition_report.xml',
        'report/purchase_requisition_report_view.xml',

        'wizard/vendor_email_views.xml',
        # 'wizard/quality_wizard.xml',
        'wizard/reject_request_reasion_views.xml',

        'views/stock_location_views.xml',
        'views/custom_material_view.xml',
        'views/purchase_requisition_view.xml',
        'views/hr_employee_views.xml',
        'views/res_company.xml',
        'views/ir_sequence_views.xml',
        'views/stock_picking_type_views.xml',
        'views/stock_picking.xml',
        'views/gsm_view.xml',
        'views/purchase_type_views.xml',
        'views/purchase_division_views.xml',
        'wizard/direct_po_from_pr_views.xml',

        'wizard/batch_requisition_view.xml',
        'wizard/batch_requisition_pr_view.xml',
        'wizard/gsm_wizard_views.xml',
        'wizard/product_stock_view.xml',

    ],

}
