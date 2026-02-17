# -*- coding: utf-8 -*-
{
    'name': 'KG Raw Fisheries Project',
    'version': '17.0',
    'summary': 'Raw Fisheries ERP',
    'description': 'Enterprise Odoo ERP Implementation for Raw Fisheries',
    'category': 'Other',
    'author': 'KG',
    'license': 'AGPL-3',
    'website': 'www.klystronglobal.com',
    'depends': ['base', 'project', 'kg_raw_fisheries_inventory'],
    'data': [
        'security/ir_rule.xml',

        'views/project_project_views.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,

}
