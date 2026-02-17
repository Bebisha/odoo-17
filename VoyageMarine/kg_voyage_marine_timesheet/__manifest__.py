# -*- coding: utf-8 -*-
{
    'name': "KG Voyage Marine Timesheet",

    "summary": "Customization for Timesheet Module",
    "version": "17.0.1.0.0",
    'category': 'Timesheet',
    'author': "Klystron Global",
    'maintainer': "SHARMI SV",
    "license": "OPL-1",
    'website': 'https://www.klystronglobal.com',
    'depends': ['base', 'timesheet_grid','sale_timesheet', 'kg_voyage_marine_crm','kg_voyage_marine_project','project', 'sale_timesheet', 'kg_voyage_marine_sale'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/time_sheet_entry_views.xml',
        'wizard/timesheet_confirm_wizard.xml',
        'wizard/menu.xml',
        'views/account_analytic_line_views.xml',
        'views/project_views.xml',
    ],

}
