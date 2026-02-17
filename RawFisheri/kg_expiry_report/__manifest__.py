# -*- coding: utf-8 -*-
{
    'name': 'KG Raw Fisheries Expiry Report',
    'version': '17.0',
    'summary': 'Raw Fisheries ERP',
    'description': 'Enterprise Odoo ERP Implementation for Raw Fisheries',
    'category': 'Other',
    'author': 'KG',
    'license': 'AGPL-3',
    'website': 'www.klystronglobal.com',
    'depends': ['base', 'hr', 'hr_contract', 'kg_raw_fisheries_hrms'],
    'data': [
        'data/ir_cron.xml',
        'views/hr_employee_passport_expiry_views.xml',
        'views/hr_employee_id_expiry_views.xml',
        'views/hr_employee_seamans_book_expiry_views.xml',
        'views/res_config_settings.xml',
        'views/menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'kg_expiry_report/static/src/**/*',
        ],
    },
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,

}
