# -*- coding: utf-8 -*-
{
    'name': "kg_casio_mass_mailing",

    'summary': """
        Mass Mailing Customization""",

    'description': """
        Mass Mailing Customization
    """,

    'author': "Mini k",
    'website': "http://www.klystronglobal.com",

    'category': 'Uncategorized',
    'version': '0.13',

    # any module necessary for this one to work correctly
    'depends': ['base','mass_mailing','kg_casio','mail','survey'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'wizard/mail_list.xml',
        'views/partner_view.xml',
        'views/unsubscribe_reason_template.xml',
        'views/unsubscribe_confirmation_template.xml',
        'views/mass_mailing.xml',
    ],
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
}
