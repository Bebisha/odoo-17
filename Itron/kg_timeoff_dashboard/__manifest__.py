{
    "name": "KG Dashboards",
    "version": "17.0.1.0.0",
    "category": "",
    "summary": """This module helps you to view leaves of employee based on
     different leave types.""",
    "description": """
    """,
    "author": "Klystron",
    "company": "",
    "maintainer": "",
    "website": "",
    "depends": ['base', "hr_holidays", "hr", "hr_attendance", "project", 'kg_contracts', 'hr_timesheet',
                'kg_itron_timesheet',
                ],
    "data": [
        'security/security.xml',

        'views/leaves_dashboard_action.xml',
        'views/leave_dashboard_views.xml',
        'views/late_dashboard.xml',
        'views/resource_pool_dashboard_views.xml',
        'views/resource_request_dashboard_view.xml',
        'views/contract_dashboard_views.xml',
        'views/timesheet_dashboard.xml',

        'views/employee.xml',
        'views/task_dashboard_views.xml',
        'views/project_task_views.xml',
        'views/helpdesk_dashboard_views.xml',
        'views/resource_request_dashboard_view.xml',

        'views/waiting_approval_dashboard_menu.xml',
        'views/dashboard_menus.xml',


    ],
    "assets": {
        "web.assets_backend": [
            'kg_timeoff_dashboard/static/src/js/waiting_approval_dashboard.js',
            'kg_timeoff_dashboard/static/src/js/timeoff_dashboard.js',
            'kg_timeoff_dashboard/static/src/js/leave_dashboard.js',
            'kg_timeoff_dashboard/static/src/js/pool_dashboard.js',
            'kg_timeoff_dashboard/static/src/js/request_dashboard.js',
            'kg_timeoff_dashboard/static/src/js/contract_dashboard.js',
            'kg_timeoff_dashboard/static/src/js/amc_dashboard.js',
            'kg_timeoff_dashboard/static/src/xml/timeoff_dashboard.xml',
            'kg_timeoff_dashboard/static/src/xml/leave_dashboard.xml',
            'kg_timeoff_dashboard/static/src/xml/resource_pool_dashboard.xml',
            'kg_timeoff_dashboard/static/src/xml/resource_request_dashboard.xml',
            'kg_timeoff_dashboard/static/src/xml/contract_dashboard.xml',
            'kg_timeoff_dashboard/static/src/xml/amc_dashboard.xml',

            'kg_timeoff_dashboard/static/src/js/late_dashboard.js',

            'kg_timeoff_dashboard/static/src/xml/late_arrival_dashboard.xml',
            'kg_timeoff_dashboard/static/src/js/timesheet_dashboard.js',
            'kg_timeoff_dashboard/static/src/xml/timesheet_dashboard.xml',
            'kg_timeoff_dashboard/static/src/js/task_dashboard.js',
            "kg_timeoff_dashboard/static/src/xml/task_dashboard.xml",
            'kg_timeoff_dashboard/static/src/js/helpdesk_dashboard.js',
            'kg_timeoff_dashboard/static/src/xml/helpdesk_dashboard.xml',
            'kg_timeoff_dashboard/static/src/xml/waiting_approval_dashboard.xml',
            'kg_timeoff_dashboard/static/src/xml/late_arrival_approve.xml',
            'kg_timeoff_dashboard/static/src/js/late_approval_dashboard.js',
            'kg_timeoff_dashboard/static/src/xml/resource_request_dashboard.xml',
            'kg_timeoff_dashboard/static/src/js/request_dashboard.js',

        ],
    },

    "images": [
    ],
    "installable": True,
    "auto_install": False,
    "application": False,
}
