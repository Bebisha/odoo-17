# -*- encoding: utf-8 -*-

{
    'name': 'Api intergration for Klystronglobal',
    'version': '17.1.1',
    'category': 'API',
    'author': 'Klystron Global',
    'description': """Api""",
    'summary': '',
    'website': 'www.klystronglobal.com',
    'images': ['static/description/icon.png'],
    'data': [
        'views/res_config_settings_view.xml',
        'views/product_views.xml',
    ],
    'depends': ['base','website','sale','website_sale'],
    'installable': True,
    'auto_install': False,
    'application': True,

}
