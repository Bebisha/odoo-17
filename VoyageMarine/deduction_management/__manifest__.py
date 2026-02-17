# -*- coding: utf-8 -*-
{
    'name': "deduction_management",


    'description': """
        Module for manage recurring deductions.
    """,

    'author': "Infintor",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '17.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr','hr_contract','mail','hr_payroll'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',

        'data/cron.xml',
        'data/element_data.xml',

        'views/views.xml',
        'views/templates.xml',
        'views/wizard_earnings_ded_view.xml',
        'views/deduction_approval_level.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],

    'installable': True,
    'auto_install': False,
    'application': False,
}
