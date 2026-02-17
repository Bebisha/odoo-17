# -*- coding: utf-8 -*-
{
    'name': "KG Raw Fisheries Payroll Report",
    'depends': ['base', 'hr', 'hr_payroll', 'kg_raw_fisheries_hrms'],
    'version': '17.0',
    'author': 'KG',
    'description': "Raw Fisheries ERP",
    'category': 'Payroll/Report',

    'data': [
        'security/ir.model.access.csv',
        'security/security_groups.xml',

        'data/ir_sequence.xml',

        'report/report.xml',
        'report/payroll_report_template.xml',
        'report/payroll_report_consolidated.xml',

        'wizard/payroll_report_wizard_views.xml',
        'wizard/crew_salary_report_wizard_views.xml',
        'wizard/menu.xml',

        'views/payroll_report_approval_views.xml',
        'views/crew_salary_report_views.xml',
        'views/final_crew_salary_monthly_views.xml',
        'views/menu.xml',
    ],

    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False
}
