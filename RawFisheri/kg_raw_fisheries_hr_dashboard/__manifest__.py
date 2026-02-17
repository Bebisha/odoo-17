# -*- coding: utf-8 -*-
{
    'name': 'KG Raw Fisheries HR Dashboard',
    'version': '17.0',
    'summary': 'Raw Fisheries ERP',
    'description': 'Enterprise Odoo ERP Implementation for Raw Fisheries',
    'category': 'Other',
    'author': 'KG',
    'license': 'AGPL-3',
    'website': 'www.klystronglobal.com',
    'depends': ['base', 'hr', 'hr_payroll', 'hr_holidays','kg_raw_fisheries_hrms'],
    'data': [
        'views/menu.xml',
    ],
    'assets': {
                'web.assets_backend': [
                    'kg_raw_fisheries_hr_dashboard/static/src/**/*',
                ],
            },
    'installable': True,
    'auto_install': False,
    'application': False,
}
