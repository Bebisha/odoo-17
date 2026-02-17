# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Gantt View Weekdays',
    'version': '17.0.0.0.0',
    'category': 'Services',
    'description': '''Gantt View with Weekdays and Weekend highlighted for Month and Week Selection''',
    'author':'Arun Reghu Kumar',
    'company': 'Tech4Logic',
    'website': 'https://tech4logic.wordpress.com/',
    "depends": ['base', 'web_gantt','project'],
    'data': [    
        
    ],
    'assets': {
        'web.assets_backend': [
            'gantt_weekdays/static/src/components/*/*.js',
            'gantt_weekdays/static/src/components/*/*.xml',

            'gantt_weekdays/static/src/css/*.css',
        ],
    },
    'images': ['static/description/banner.gif'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
