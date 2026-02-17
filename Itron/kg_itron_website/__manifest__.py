# -*- encoding: utf-8 -*-

{
    'name': 'Itron contact us Website for Klystronglobal',
    'version': '17.1.1',
    'category': 'Itron Website',
    'author': 'Klystron Global',
    'description': """Itron Website""",
    'summary': '',
    'website': 'www.klystronglobal.com',
    'images': ['static/description/icon.png'],
    'data': [
        'views/ai_portal_template.xml',
        'views/kiosks_portal_template.xml',
        'views/odoo_portal_template.xml',
        'views/devops_portal_template.xml',
        'views/payment_portal_template.xml',
        'views/seo_portal_template.xml',
        'views/testing_portal_template.xml',
        'views/contact_us_views.xml',
    ],
    'depends': ['website','crm','kg_crm'],
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 105,
    'license': 'AGPL-3',
}
