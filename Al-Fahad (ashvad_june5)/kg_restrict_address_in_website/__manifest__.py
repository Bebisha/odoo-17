{
    'name': 'Restrict Address in Website',
    'version': '17.0.1.0.0',
    'summary': """Restrict Address in Website""",
    'description': """Restrict Address in Website""",
    'author': 'Klystron Global',
    'maintainer': 'Binu A R',
    'website': "https://www.klystronglobal.com/",
    # 'images': ["static/description/banner.png"],

    'category': '',
    'sequence': 1,
    'depends': ['base', 'website_sale'],
    'data':[
        # 'views/sale_order_views.xml',
        'views/restrict_address_website_sale.xml',
    ],
    # 'assets': {
    #     'web.assets_backend': [
    #         'kg_systray_icon/static/src/js/systray_icon.js',
    #         'kg_systray_icon/static/src/xml/systray_icon.xml',
    #     ],
    # },
    'installable': True,

}
