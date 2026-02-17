# -*- coding: utf-8 -*-
{
    'name': 'KG Raw Fisheries Negative Leave Allocation',
    'version': '17.0',
    'summary': 'Raw Fisheries ERP',
    'description': 'Enterprise Odoo ERP Implementation for Raw Fisheries',
    'category': 'Other',
    'author': 'KG',
    'license': 'AGPL-3',
    'website': 'www.klystronglobal.com',
    'depends': ['base', 'hr', 'hr_payroll', 'kg_raw_fisheries_hrms'],
    'data': [
        'security/ir.model.access.csv',
        'reports/negative_leave_balance_report_view.xml',
        'reports/negative_leave_balance_report.xml',
        # 'views/hr_employee.xml',
        'views/hr_leave_allocation.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,

}
