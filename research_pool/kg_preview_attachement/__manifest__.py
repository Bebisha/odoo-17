# -*- coding: utf-8 -*-

# Klystron Global LLC
# Copyright (C) Klystron Global LLC
# All Rights Reserved
# https://www.klystronglobal.com/


{
    'name': "Many2Many Attachment Preview",
    'version': '17.0.1.0.0',
    'summary': """Preview the attachment in Many2Many field""",
    'description': """"This module helps you to preview the attachments in
        Many2Many fields.""",
    'author': 'Klystron Global',
    'maintainer': 'Bebisha C P',
    'website': "https://www.klystronglobal.com/",
    'category': 'sale',
    'version': '17.0.0.1',
    'license': 'AGPL-3',
    'depends': ['sale', 'mail', 'base'],
    'data': [
        'views/preview_attachement.xml'
    ],
    # 'assets': {
    #     'web.assets_backend': [
    #         'kg_preview_attachement/static/src/**/*',
    #     ],
    # },
    # 'assets': {
    #     'web.assets_backend': [
    #         'kg_preview_attachement/static/src/js/preview_attachement.js',
    #         'kg_preview_attachement/static/src/xml/preview_attach_views.xml',
    #     ],
    # },
}
