# -*- coding: utf-8 -*-

# Klystron Global LLC
# Copyright (C) Klystron Global LLC
# All Rights Reserved
# https://www.klystronglobal.com/


{
    'name': ' Manage membership',
    'summary': """
          Manage membership""",
    'description': """
             Manage membership inside the odoo""",
    'author': 'Klystron Global',
    'maintainer':'Bebisha C P',
    'website': "https://www.klystronglobal.com/",
     'category': 'membership',
    'version': '17.0.0.1',
    'license': 'AGPL-3',
    'depends': ['base', 'membership','product','contacts'],
    'data': [
        # 'security/ir.model.access.csv',
        # 'wizard/purchase_views.xml',
        'data/portal_registration_menu.xml',
        'data/sequence_views.xml',
        'views/membership_form_portal_views.xml',
        'views/membership_views.xml',
        'views/res_partner_views.xml',



    ],

}
