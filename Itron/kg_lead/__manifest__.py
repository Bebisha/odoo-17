# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'KG Leads',
    'version': '17.0.1.0.0',
    'category': '',
    'summary': '',
    'description': """KG Leads""",
    'depends': ['kg_crm', ],
    'data': [
        'security/ir.model.access.csv',
        'security/groups.xml',
        'data/data.xml',
        'views/kg_lead_views.xml',
        'views/crm_stage_views.xml',
        'views/crm_lead_views.xml',
    ],

    'sequence': -1,
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
