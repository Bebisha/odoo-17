# -*- coding: utf-8 -*-
{
    'name': "KG Voyage Marine CRM",

    "summary": "Customization for CRM Module",
    "version": "17.0.1.0.0",
    'category': 'CRM',
    'author': "Klystron Global",
    'maintainer': "SHARMI SV",
    "license": "OPL-1",
    'website': 'https://www.klystronglobal.com',
    'depends': ['base', 'crm', 'sale_crm', 'mail', 'purchase','product','hr','stock','kg_voyage_marine_inventory'],
    'data': [
        'security/ir.model.access.csv',
        'data/documents.xml',
        'data/sequence.xml',
        'data/server_action.xml',
        'data/activity.xml',
        'data/opeartion_type.xml',

        'views/crm_lead_views.xml',
        'views/crm_estimation_type_views.xml',
        'views/crm_estimation_views.xml',
        'views/res_config_settings_views.xml',
        'views/crm_material_cost_views.xml',
        'views/crm_estimation_items_views.xml',
        'views/crm_labour_cost_views.xml',
        'views/crm_other_cost_views.xml',
        'views/vessel_form_views.xml',
        'views/enquiry_reference_views.xml',
        'views/inspection_calibration_vies.xml',
        'views/seq_lot_views.xml',
        'views/stock_views.xml',
        'views/inspection_report_views.xml',

        'wizard/create_rfq_wizard_views.xml',
        'wizard/inspection_confirmation_wizard_views.xml',

        'report/job_receipt_note.xml',
        'report/report_inspection_tmp_views.xml',
        'report/condition_report_template.xml',
        'report/report_inspection_tmp_check_list_views.xml',
        'report/report_inspection_tmp_out_views.xml',
        'report/inspection_report_template.xml',
        'report/report.xml',

    ],

}
