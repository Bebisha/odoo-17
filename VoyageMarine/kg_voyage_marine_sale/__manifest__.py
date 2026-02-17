# -*- coding: utf-8 -*-
{
    'name': "KG Voyage Marine Sales",

    "summary": "Customization for Sales Module",
    "version": "17.0.1.0.0",
    'category': 'Sales',
    'author': "Klystron Global",
    'maintainer': "SHARMI SV",
    "license": "OPL-1",
    'website': 'https://www.klystronglobal.com',
    'images': ['static/description/watermark.png'],
    'depends': ['base', 'sale_management', 'stock', 'kg_voyage_marine_crm', 'survey', 'sale_project', 'crm', 'product','sale_margin',
                'sale',
                'account_accountant', 'hr', 'industry_fsm', 'mrp', 'contacts', 'mail', 'kg_purchase','account','sale_renting',
                'sale_pdf_quote_builder', 'material_purchase_requisition', 'purchase', 'kg_voyage_marine_crm',
                'kg_voyage_marine_inventory'],
    'data': [
        'security/ir.model.access.csv',

        'data/activity.xml',
        'data/mail_template.xml',
        'data/paper_format.xml',
        'data/sequence.xml',
        'data/server_action.xml',
        'data/processing_documents_data.xml',

        'report/service_report.xml',
        'report/order_acknowledgement_report.xml',
        'report/report.xml',
        'report/commercial_invoice_report_view.xml',
        'report/quotation_report.xml',
        'report/so_report.xml',
        'report/job_costing_report.xml',
        'report/sales_order_report.xml',
        'report/slae_report_views.xml',

        'views/res_config_settings_views.xml',
        'views/processing_documents_views.xml',
        'views/sale_order_views.xml',
        'views/res_partner_views.xml',
        'views/account_payment_terms_views.xml',
        'views/res_partner_bank_views.xml',
        'views/supplier_category_views.xml',
        'views/divisions_views.xml',
        'views/sale_terms_conditions.xml',
        'views/purchase_order_views.xml',
        'views/packing_list_views.xml',
        'views/delivery_terms_views.xml',
        'views/product_template_views.xml',
        'views/manufaturing_master_view.xml',
        'views/material_requisition_views.xml',
        'views/mrp_production_views.xml',
        'views/account_move_views.xml',

        'wizard/revision_reason_wizard_views.xml',
        # 'wizard/job_costing_views.xml',
        'wizard/feedback.xml',
        'wizard/add_section_wizard.xml',
        'wizard/edit_section_wizard.xml',
        'wizard/non_in_ml_line_views.xml',
        'wizard/create_rfq_wizard_views.xml',
        'wizard/sale_order_confirm_wizard_views.xml',
        'wizard/crm_rq_views.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'kg_voyage_marine_sale/static/scss/section_note_widget.scss'
        ],
    }

}
