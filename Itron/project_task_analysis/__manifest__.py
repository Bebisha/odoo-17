# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Task Analysis',
    'version': '17.0.1.0.0',
    'category': '',
    'summary': '',
    'description': """""",
    'depends': ['hr_timesheet', 'kg_project_milestone','project',
                'base','sale','account','web','mail','hr'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',

        'data/data.xml',
        'data/cron.xml',
        'data/product_data.xml',

        'view/project_views.xml',
        'view/task_analysis_view.xml',
        'view/project_team.xml',
        'view/project_milestone_status_view.xml',


        'view/resource_pool.xml',
        'view/res_settings.xml',

        'wizard/extended_wizard.xml',
        'wizard/reject_reason.xml',
        'wizard/daily_task_view.xml',
        'report/taskwise_analysis.xml',
    ],
    'sequence': -1,
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
