# -*- coding: utf-8 -*-

{
    'name': "KG Earnings And Deductions",
    'depends': ['base', 'hr', 'hr_payroll','hr_contract','mail','kg_raw_fisheries_hrms'],
    'version': '17.0',
    'author': 'KG',
    'description': "KG Earnings And Deductions",
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'views/hr_earnings_deduction_views.xml',
        'views/earn_ded_elements_views.xml',
        'views/menu.xml',
    ],

    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False
}