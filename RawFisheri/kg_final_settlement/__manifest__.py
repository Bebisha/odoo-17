# -*- coding: utf-8 -*-
{
    'name': "KG Raw Fisheries Final Settlement",
    'depends': ['base', 'hr', 'hr_payroll', 'kg_raw_fisheries_hrms'],
    'version': '17.0',
    'author': 'KG',
    'description': "Raw Fisheries ERP",
    'category': 'Employee/Resignation',

    'data': [
        'security/ir.model.access.csv',
        'report/gratuity_report.xml',
        'report/gratuity_report_template.xml',
        'data/ir_sequence.xml',
        # 'views/hr_contract.xml',
        'views/hr_resignation.xml',
        'views/menu.xml',
    ],

    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False
}
