# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'KG Contract',
    'version': '17.0.1.0.0',

    'category': '',
    'summary': '',
    'description': """""",
    'depends': ['base', 'sale',
                'account','project','product','subscription_package','sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/data.xml',
        'data/cron.xml',
        'data/product_data.xml',
        # 'view/task_analysis_view.xml',
        # 'view/resource_pool.xml',
        'view/contract_request.xml',
        'view/project.xml',
        # 'view/project_milestone_status_view.xml',
        # 'view/res_settings.xml',
        'wizard/offshore_engagement.xml',
        # 'wizard/extended_wizard.xml',
        # 'wizard/signature_wizard.xml',
        # 'wizard/reject_reason.xml',
        # 'report/taskwise_analysis.xml',
        # 'report/report_invoice.xml',

    ],
    'sequence': -1,
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
