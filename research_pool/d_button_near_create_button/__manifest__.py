{
    'name': "Button Near Create Button",
    'summary': "Button Near Create Button",

    'description': """
WHAT IT DOES
============

This module create a button near create button in the list view then we will try to execute one method or some methods for this button

Editions Supported
==================
1. Community Edition
2. Enterprise Edition

    """,
    'author': "Duong Nguyen (daiduongnguyen2709@gmail.com)",
    'website': "daiduongnguyen2709@gmail.com",
    'support': "daiduongnguyen2709@gmail.com",
    'sequence': 24,
    'category': 'Tutorials',
    'version': '0.1.1',
    'depends': ['project' ,'crm'],

    # always loaded
    'data': [
        'views/project_views.xml'
    ],
    'assets': {
        'web.assets_backend': [
            '/d_button_near_create_button/static/src/views/*/*',
        ],
    },
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'price': 0.0,
    'currency': 'EUR',
    'license': 'OPL-1',
}
