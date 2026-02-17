# -*- coding: utf-8 -*-
{
    'name': "kg_casio",

    'summary': """
        Casio customisation from version 13 to 17.
        Including API integration""",

    'description': """
        *Customer details
        *API
        *Helpdesk
    """,

    'author': "Binu A R",
    'website': "http://www.klystronglobal.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'CRM',
    'version': '17.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base','crm','survey','helpdesk','mass_mailing'],

    # always loaded
    'data': [
        'data/data.xml',
        'security/ir.model.access.csv',
        'views/company_view.xml',
        'views/views.xml',
        'views/templates.xml',
        'views/birthday_mail_scheduler.xml',
        'views/welcome_mail_template.xml',
        'views/birthday_template.xml',

        'views/mass_mailing_templates.xml',
        'views/partner_view.xml',
        'views/kg_voucher_view.xml',
        'views/customer_inv_view.xml',
        'views/booking_details_view.xml',
        'views/helpdesk_view.xml',
        'views/promo_code_view.xml',
        'views/link_tracker_click_view.xml',
        'wizards/customer_import.xml',
        'views/mass_mailing_view.xml',
        'views/login_screen.xml',
        'security/security.xml',
        'wizards/customer_import.xml'

    ],
}
