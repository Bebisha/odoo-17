{
    'name': 'G-Shock Webpage Page',
    'version': '17.1.1',
    'website': 'www.klystronglobal.com/',
    'description': """ """,
    'depends': ['base', 'website','kg_casio'],
    'category': 'Website',
    'data': [
         'views/template.xml',
         'views/join_gmusic_template.xml',
         'views/gmusic_scan_template.xml',
         'views/scan_template.xml',
         'views/page.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'kg_gshock_page/static/src/css/style.css',
            'kg_gshock_page/static/src/js/template.js',
        ],
    },

    'application': True,
    'installable': True,
    'license': 'LGPL-3',
}
