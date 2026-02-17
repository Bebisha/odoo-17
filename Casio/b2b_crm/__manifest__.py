{
    'name': 'B2B CRM Module',
    'version': '17.0.1.0.0',
    'summary': 'Customizations for CRM',
    'sequence': 100,
    'description': 'This module enhances CRM functionalities.',
    'author': 'Binu',
    'depends': ['base', 'crm','sale',],
    'data': [

        'views/b2b_views.xml',

    ],
    'installable': True,
    'application': True,
}