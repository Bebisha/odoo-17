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
    'depends': ['base', 'hr', 'event', 'board','crm','bista_tdcc_announcement'],
    'data': [
        'views/dashboard_views.xml',

    ],
    'assets': {
        'web.assets_backend': [
            'bista_hr_dashboard/static/src/js/dashboard.js',
            'bista_hr_dashboard/static/src/xml/dashboard.xml',
            'bista_hr_dashboard/static/src/css/dashboard.css',

        ],
    },
}
