# -*- coding: utf-8 -*-
# Copyright 2020 - Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
{
    'name': 'Odoo CRM Facebook Leads | Facebook Page Leads Connector',
    'category': 'CRM',
    'description': 'Generate Leads from Facebook Ad Campaign to Odoo CRM',
    'summary': 'Generate Leads from Facebook Ad Campaign to Odoo CRM',
    'version': '1.0',
    'depends': [
        'crm','kg_crm'
    ],
    'data': [
        # Security Code
        'security/ir.model.access.csv',
        # Views
        'views/facebook_credentials.xml',
        'views/facebook_page.xml',
        'views/facebook_lead_form.xml',
        'views/default_fields_mapping.xml',
        'views/facebook_lead_form.xml',
        # CRON
        'data/ir_cron.xml',
        # Data
        'data/lead.form.default.mapping.csv',
    ],
    # Author
    'license': 'OPL-1',
    'author': 'TechKhedut Inc.',
    'website': 'https://TechKhedut.com',
    'images': ['static/description/cover.png'],
    'price': 49,
    'currency': 'EUR',
    'installable': True,
    'application': False,
    'auto_install': False,
}
