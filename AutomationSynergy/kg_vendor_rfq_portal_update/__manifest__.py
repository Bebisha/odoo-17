# -*- coding: utf-8 -*-

# Klystron Global LLC
# Copyright (C) Klystron Global LLC
# All Rights Reserved
{
    'name': 'RFQ Portal Update',
    'summary': """
        RFQ Portal Update""",
    'description': """
         Allow vendors to update RFQ through the portal""",
    'author': 'Klystron Global',
    'maintainer': 'Sumayya P P',
    'website': "https://www.klystronglobal.com/",
    'category': 'Purchase',
    'version': '17.0.0.1',
    'license': 'AGPL-3',
    'depends': ['purchase', 'base','portal','web'],
    'data': [
        'views/portal_templates.xml',
    ],
}
