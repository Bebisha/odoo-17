# -*- coding: utf-8 -*-
{
    'name': "kg_project_milestone",

    'summary': """
        project milestone""",

    'description': """
        This module using to customise project milestone
    """,

    'author': "klystron Global",
    'website': "www.klystronglobal.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'itron',
    'version': '17.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base','project','project_task_default_stage'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/cron.xml',

        'views/project_timeline.xml',
        'views/milestone_views.xml',
        'views/project_view.xml',
        'views/project_team.xml',

        'wizard/project_update_wizard.xml',
        'wizard/project_status_update_wizard.xml',
        # 'wizard/update_milestone_wizard.xml',

        'report/report.xml',
        'report/project_milestone_line_report.xml',
        'report/project_milestone_line_templates.xml',
        'report/project_status_updates_report.xml',
    ],
     # 'images': ['static/description/icon.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
