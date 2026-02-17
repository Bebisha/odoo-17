# -*- coding: utf-8 -*-

# Klystron Global LLC
# Copyright (C) Klystron Global LLC
# All Rights Reserved
# https://www.klystronglobal.com/

{
    'name': 'KG Gant Chart',
    'version': '17.0.1.0.0',
    'license': 'LGPL-3',
    'depends': ['base','sale','purchase','stock','web_gantt','project','project_enterprise'],
    'sequence': '-100',
    'author': 'Klystron Global',
    'maintainer': 'Dojy Larsan',
    'website': "www.klystronglobal.com",
    'application': True,
    'description': """The Module provide Some Customization in Odoo Gantt View for Project Module""",
    'data': [
        'views/project_task_gantt_views.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'kg_gantt_chart/static/src/components/gannt_renderer.js',
            'kg_gantt_chart/static/src/components/gantt_renderer.xml',
        ]},
    "installable": True,
    'demo': [],

}