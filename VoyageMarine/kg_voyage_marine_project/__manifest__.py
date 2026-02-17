{
    'name': "KG Voyage Marine Project",

    "summary": "Customization for Project Module",
    "version": "17.0.1.0.0",
    'category': 'Project, Task',
    'author': "Klystron Global",
    'maintainer': "SHARMI SV",
    "license": "OPL-1",
    'website': 'https://www.klystronglobal.com',
    'depends': ['base', 'project', 'kg_voyage_marine_crm', 'sale_project', 'kg_voyage_marine_sale',
                'project_enterprise', 'web_gantt', 'industry_fsm_sale', 'kg_gantt_chart'],

    'data': [
        'security/ir.model.access.csv',
        # 'data/ir_cron.xml',

        'views/project_project_views.xml',
        # 'views/res_users_views.xml',
        'views/project_task_views.xml',
        'views/project_team.xml',
    ],

    'assets':
        {'web.assets_backend': [
            'kg_voyage_marine_project/static/src/js/project_task_gantt.js',
        ]
        },

}
