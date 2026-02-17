# -*- coding: utf-8 -*-
{
    'name': "Custom Survey Report",

    'summary': """
        Its used for print the Survey Questioning report""",

    'description': """
        Its used for print the Survey Questioning report
    """,

    'author': "Ameen KG",
    'website': "http://www.klystronglobal.com",


    'category': 'Survey',
    'version': '17.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': [
        'base', 'survey',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'wizard/wizard_view.xml'

    ],
    'qweb': [],
    'demo': [
    ],
    'application': True,
    'installable': True,
}