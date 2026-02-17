# -*- coding: utf-8 -*-
{
    'name': "Operating Unit",

    "summary": "An operating unit (OU) is an organizational entity part of a",
    "version": "17.0.1.0.0",
    'category': 'Purchase',
    'author': "Klystron Global",
    'maintainer': "SHARMI SV",
    "license": "OPL-1",
    'website': 'https://www.klystronglobal.com',
    # any module necessary for this one to work correctly
    'depends': ['base'],
    # always loaded
    'data': [
        "security/operating_unit_security.xml",
        "security/ir.model.access.csv",
        "data/operating_unit_data.xml",
        "view/operating_unit_view.xml",
        "view/res_users_view.xml",
    ],
    "demo": ["demo/operating_unit_demo.xml"],

}
