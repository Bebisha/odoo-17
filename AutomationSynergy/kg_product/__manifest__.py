{
    'name': 'Kg Product',
    'version': '17.0.1.0.0',
    'summary': 'Customizations for Product Template',
    'sequence': 100,
    'description': 'This module enhances Product functionalities.',
    'author': 'Klystron Global',
    'maintainer': 'Binu A R',
    'license': 'LGPL-3',

    'depends': ['base', 'stock', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_brand_views.xml',
        'views/product_model_views.xml',
        'views/product_template_views.xml',
    ],
    'installable': True,
    'application': True,
}
