# -*- coding: utf-8 -*-

# Klystron Global LLC
# Copyright (C) Klystron Global LLC
# All Rights Reserved
# https://www.klystronglobal.com/


{
    'name': 'Employee Documents Expiry Management',
    'summary': """Manages Employee Documents With Expiry Notifications.""",
    'description': """
        The system efficiently manages employee-related documents, including expiration notifications. It automatically sends alerts to relevant employees as expiry dates approach. These timely notifications enable proactive measures to update or renew documents, mitigating potential legal, regulatory, or operational issues stemming from expired documentation.""",
    'author': 'Klystron Global',
    'maintainer': 'Bebisha C P',
    'website': "https://www.klystronglobal.com/",
    'category': 'Employee',
    'version': '17.0.0.1',
    'license': 'AGPL-3',
    'depends': ['hr', 'base', 'mail','sale'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'views/employee_document_type_views.xml',
        'views/hr_employee_document_views.xml',
        'views/hr_employee_views.xml',



    ],
    "assets": {
        "web.assets_backend": [
            "kg_employee_document_management/static/src/xml/PreviewButtonViews.xml",
            "kg_employee_document_management/static/src/js/PreviewButton.js "
        ],
    },
}
