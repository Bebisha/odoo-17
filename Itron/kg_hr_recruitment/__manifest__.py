# -*- coding: utf-8 -*-
{
    'name': "KG HR Recruitment",
    'version': '17.0.1.0.0',
    'depends': ['base', 'hr_recruitment','website_hr_recruitment'],
    'author': 'klystron',
    'description': "customization hr recruitment",
    'maintainer': "klystron",
    'category': 'hr/recruitment',

    'data': [
        'security/res_groups.xml',
        'data/website_menu.xml',
        'data/ir_sequence.xml',
        'report/generate_ae_final_offer_letter.xml',
        'report/generate_ae_offer_letter.xml',
        'report/generate_final_offer_letter.xml',
        'report/generate_offer_letter.xml',
        'report/action_offer_letter_report.xml',
        'wizard/mail_compose_message_views.xml',
        'views/hr_applicant_views.xml',
        'views/hr_jobs.xml',
        'views/hr_recruitment_stages_views.xml',
        'views/website_hr_recruitment_templates.xml',
        'views/website_job_portal_template.xml',
    ],

    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False
}
