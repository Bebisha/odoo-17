# -*- coding: utf-8 -*-
{
    'name': "TDCC API",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
       TDCC API Integration
    """,

    'author': "Klystron Global",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '17.1.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base', 'portal'
               ],

    # always loaded
    'data': [

        'data/sequence_data.xml',
        'views/patient_additional_demographic.xml',
        'views/next_of_kin.xml',
        'views/patient_visit.xml',
        'views/pv_additional_information.xml',
        'views/observation_result.xml',
        'views/patient_allergy_information.xml',
        'views/diagnosis.xml',
        'views/diagnosis_related_grp_segment.xml',
        'views/procedures_segment.xml',
        'views/guarantor_segment.xml',
        'views/insurance.xml',
        'views/patient_merge.xml',
        'views/common_order.xml',
        'views/observation_request.xml',
        'views/message_acknowledgement.xml',
        'views/z_segment_consent.xml',
        'views/segment_social_history.xml',
        'views/segment_family_history.xml',

        'views/api_menus.xml',
        'security/ir.model.access.csv',

    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],

    'assets': {


    },


}
