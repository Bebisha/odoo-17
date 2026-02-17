# -*- coding: utf-8 -*-
{
    'name': "KG Raw Fisheries Dashboard",
    'version': '17.0.1.0.0',
    'depends': ['base', 'kg_raw_fisheries_entries'],
    'author': 'Ashvad',
    'description': "KG Raw Fisheries Dashboards for displaying real-time updates.",
    'maintainer': "Ashvad",
    'category': 'Raw Fisheries/dashboard',

    'data': [
        'views/menu.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'kg_raw_fisheries_dashboard/static/src/js/inventory_updates.js',
            'kg_raw_fisheries_dashboard/static/src/js/vessel_revenue.js',
            'kg_raw_fisheries_dashboard/static/src/xml/inventory_updates_template.xml',
            'kg_raw_fisheries_dashboard/static/src/xml/vessel_revenue_template.xml',
        ],
    },

    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False
}
