{
    'name': 'HR Dashboard',
    'version': "17.1.1",
    'license': 'LGPL-3',
    'category': 'HR',
    'description': """
    HR Dashboard
    """,
    'author': 'Bista Solutions Pvt. Ltd.',
    'website': 'http://www.bistasolutions.com',
    'depends': ['base', 'hr', 'event', 'board','crm'],
    'data': [
        'views/dashboard_views.xml',

    ],
    'assets': {
        'web.assets_backend': [
            'bista_dashboard_hr/static/src/js/dashboard.js',
            'bista_dashboard_hr/static/src/xml/dashboard.xml',
            'bista_dashboard_hr/static/src/css/dashboard.css',

        ],
    },
}
