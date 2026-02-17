# -*- coding: utf-8 -*-
{
    'name': "KG HR Employee",
    'author': "Klystron Global",
    'website': "http://www.klystronglobal.com",
    'category': 'sales',
    'version': '17.0.1.0.0',
    'depends': ['base', 'crm', 'sale', 'mail', 'project', 'kg_project_milestone', 'hr_contract','hr'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/activity_data.xml',
        'data/template_birthday_data.xml',
        'data/hr_holidays_data.xml',
        'data/cron.xml',
        'data/sequence.xml',
        'views/hr_employee.xml',
        'views/project.xml',
        'views/account_move.xml',
        'views/hr_leave.xml',
        'views/hr_contract.xml',
        'views/res_settings.xml',
        'views/kg_designation.xml',
    ],
    "installable": True,
    'demo': [
        'demo/demo.xml',
    ],
}
