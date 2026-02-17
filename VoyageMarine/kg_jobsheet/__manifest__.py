# -*- coding: utf-8 -*-

# Klystron Global LLC
# Copyright (C) Klystron Global LLC
# All Rights Reserved
{
    'name': 'Job Sheet Master',
    'summary': """
        Job Sheet Master module""",
    'description': """
        Job Sheet Master""",
    'author': 'Klystron Global',
    'maintainer': 'Bebisha C P',
    'website': "https://www.klystronglobal.com/",
    'category': 'Purchase',
    'version': '17.0.0.1',
    'license': 'AGPL-3',
    'depends': ['base','stock', 'product','repair','kg_voyage_marine_inventory','kg_voyage_marine_sale','material_purchase_requisition','crm'],
    'data': [
        'data/sequence_views.xml',
        'data/product_category_data.xml',
        'data/location_views.xml',
        'data/activity.xml',

        'security/ir.model.access.csv',

        'views/menu_views.xml',
        'views/equipment_views.xml',
        'views/equipment_catgeory_views.xml',
        'views/calabration_form_views.xml',
        'views/lsa_form_views.xml',
        'views/ffa_form_views.xml',
        'views/certificate_views.xml',
        'views/product_category_views.xml',
        'views/repair_views.xml',
        'views/sale_views.xml',
        'views/product_template_views.xml',
        'views/master_equipment_catgeory.xml',
        'views/work_instruction_views.xml',
        'views/standard_used_views.xml',
        'views/navigation_communication_views.xml',
        'views/field_service_views.xml',
        # 'views/seq_lo_views.xml',
        # 'views/vessel_form_views.xml',
        'report/ir_action_report.xml',
        'report/calibration_dimension_report.xml',
        'report/final_certifcate.xml',
        'report/lsa_certificate.xml',
        'report/ffa_certificate.xml',
        'report/final_ffa_certificate.xml',
        'report/final_certifcate_lsa.xml',
        'report/field_service_certificate.xml',
        'report/final_field_service_certificate.xml',
        'report/final_navigation_communication_certificate.xml',
        'report/navigation_communication_certificate.xml',
    ],
}
