# -*- coding: utf-8 -*-
{
    'name': "developing_child_centre",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '17.1.1',
    'application': True,
    "license": "AGPL-3",

    # any module necessary for this one to work correctly
    'depends': ['base','bista_tdcc_operations'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/templates.xml',
        'views/developmental_history_form.xml',
        'views/developmental_history_form_frontend.xml',
        'views/client_intake_form.xml',
        'views/client_intake_form_frontend.xml',
        # 'views/child_patient_form_inherit.xml',
        'data/sequence.xml',
        'data/mail_template.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],

    'assets': {

        'web.assets_frontend': [
            'static/src/js/condition.js',
        ],

    },


}
