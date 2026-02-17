# -*- coding: utf-8 -*-
{
    'name': "Estimation",
    'category': 'sales',
    'version': '17.0.1.0.0',
    'license': 'LGPL-3',
    'depends': ['base', 'crm', 'sale', 'mail','project','sale_project','hr_timesheet'],
    'author': "Klystron Global",
    'website': "http://www.klystronglobal.com",
    'data': [
        'security/ir.model.access.csv',
        'data/activity_data.xml',
        'views/estimation_view.xml',
        'views/sale.xml',
        'views/project_view.xml',
    ],
     "installable": True,
    'demo': [
        'demo/demo.xml',
    ],
}
