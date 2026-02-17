# -*- coding: utf-8 -*-

# Klystron Global LLC
# Copyright (C) Klystron Global LLC
# All Rights Reserved

{
    'name': 'Purchase Revision',
    'version': "17.0.0.1",
    'description': """Revisions and Versions for Purchase Orders and Quotations""",
    'author': "Klystron Global",
    'depends': ['base', 'purchase'],
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_order_views.xml',
        'wizards/revision_wizard.xml'
    ],
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
}
