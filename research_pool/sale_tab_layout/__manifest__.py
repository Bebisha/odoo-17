# -*- coding: utf-8 -*-
{
    'name': "KG Sales",

    "summary": "Customization for Sales Module",
    "version": "17.0.1.0.0",
    'category': 'Sales',
    'author': "Klystron Global",
    'maintainer': "Bebisha C P",
    "license": "OPL-1",
    'website': 'https://www.klystronglobal.com',
    'images': ['static/description/watermark.png'],
    'depends': ['base', 'sale_management',
                'sale', ],
    'data': [
        'security/ir.model.access.csv',
        'report/aricraft_template.xml',
        'report/report.xml',
        'views/sale_views.xml',
        'wizard/add_section_wizard.xml',


        #
        # 'data/activity.xml',
        # 'data/mail_template.xml',
        # 'data/paper_format.xml',
        # 'data/sequence.xml',
    ]
}
