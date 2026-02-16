# -*- coding: utf-8 -*-
{
    'name': "Image Preview Zoom",

    'summary': "Click on the image to enlarge the preview",

    'description': """
Click on the image to enlarge the preview, The usage method is exactly the same as that of image widget
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/17.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Extra Tools',
    'version': '0.1',
    'license': 'LGPL-3',
    # any module necessary for this one to work correctly
    'depends': ['base', 'web','sale'],
    'images': ['static/description/banner.jpg'],
    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/views.xml',
        'views/preview_attachement.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'image_preview_zoom/static/src/views/fields/image_preview/image_preview.xml',
            'image_preview_zoom/static/src/views/fields/image_preview/image_preview.js',
        ],
    },
}

