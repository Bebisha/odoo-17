{
    'name': 'User Access Report',
    'version': '17.0.1.0.0',
    'summary': 'Export user-level access rights report to Excel',
    'category': 'Reporting',
    'website': 'www.klystronglobal.com',
    'license': 'LGPL-3',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',

        'wizard/user_access_wizard_views.xml',
    ],
    'installable': True,
    'application': False,
}
