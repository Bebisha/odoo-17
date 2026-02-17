# -*- encoding: utf-8 -*-
#
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
#

{
    'name': 'Bista HR',
    'version': '17.1.1',
    'category': 'HR',
    'description': """
Bista HR
===========
    * Manage employee details.
    """,
    'author': 'Bista Solutions Pvt. Ltd.',
    'website': 'http://www.bistasolutions.com',
    'depends': ['base', 'hr', 'hr_contract', 'product','account',
                'hr_recruitment', 'base_address_extended'],
    'data': [
        "security/hr_security.xml",
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "data/employee_master_data.xml",
        "data/employee_email_template.xml",
        "views/hr_master_view.xml",
        'views/res_config.xml',
        'views/res_bank_view.xml',
        'reports/employee_information.xml',
        'reports/report_register.xml',
    ],
    'installable': True,
    'auto-install': True,
    'license': 'LGPL-3',
}
