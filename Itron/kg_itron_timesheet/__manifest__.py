# -*- coding: utf-8 -*-
{
    'name': "KG Itron Timesheet",

    'summary': """
        Customization in timesheet""",

    'description': """
        Customization in timesheet
    """,

    'author': "Klystron Global",
    'website': "http://www.yourcompany.com",

    'category': 'Project',
    'version': '17.0.1.0.0',

    'depends': ['base', 'hr_timesheet', 'kg_project_milestone'],

    'data': [
        'security/ir.model.access.csv',
        'security/hr_timesheet_security.xml',
        'wizard/employee_timesheet_date_wise.xml',
        # 'data/ir_cron.xml',
        'views/project_task_views.xml',
        'views/timesheet.xml',
        'views/res_settings.xml',
        'views/employee_date_wise_timesheet.xml',
        'views/timesheet_analysis_report.xml',
        # 'views/timesheet_missing.xml',
        'report/timesheet_reports.xml',
        'report/timesheet_templates.xml',
        'report/employee_timesheet_report.xml',
        'wizard/timesheet_report_views.xml',
        'wizard/timesheet_datewise_view.xml',
        # 'wizard/employee_timesheet_report_wizard_views.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'kg_itron_timesheet/static/src/views/pivot/pivot_renderer.xml',
        ]
    },
}
