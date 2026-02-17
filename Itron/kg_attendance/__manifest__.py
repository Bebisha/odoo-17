# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Attendance',
    'version': '17.0.1.0.0',
    'category': '',
    'summary': '',
    'description': """Attendance""",
    'depends': ['base', 'hr', 'hr_attendance', 'mail', ],
    'data': [
        'security/ir.model.access.csv',
        'security/record_rules.xml',
        'data/sequence.xml',
        'data/ir_cron.xml',
        'views/attendance_views.xml',
        'views/thank_you_template.xml',
        'views/early_late_request_views.xml',
        # 'views/late_dashboard.xml',
        # 'views/config.xml',
        'wizard/attendance_report.xml',
        'wizard/late_report_views.xml',
        'wizard/reject_reason_wizard.xml',

    ],
    "assets": {
        "web.assets_backend": [
            # 'kg_attendance/static/src/js/late_dashboard.js',
            #
            # 'kg_attendance/static/src/xml/late_arrival_dashboard.xml',

        ],
    },
    'sequence': -1,
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
