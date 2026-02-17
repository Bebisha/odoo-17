# -*- coding: utf-8 -*-
{
    'name': 'KG Raw Fisheries Leave Settlement',
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
        'data/ir_sequence.xml',
        'reports/leave_settlement_report.xml',
        'reports/report.xml',
        'views/hr_leave.xml',
        'views/leave_settlement_views.xml',
        'views/menu.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,

}
