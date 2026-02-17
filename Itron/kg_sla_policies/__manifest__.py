# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'SLA Policies',
    'version': '17.0.1.0.0',
    'category': '',
    'summary': '',
    'description': """""",
    'depends': ['hr_timesheet','project',
                'base','sale','web','mail','hr','helpdesk_mgmt'],
    'data': [
        'security/ir.model.access.csv',
        'security/sla_security.xml',
        'report/sla_report_analysis_views.xml',

        'views/helpdesk_sla_view.xml',
        'views/helpdesk_ticket_type_view.xml',
        'views/helpdesk_ticket_team_view.xml',
        'views/helpdesk_ticket_view.xml',
        'views/res_partner.xml',
    ],
    'sequence': -1,
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
