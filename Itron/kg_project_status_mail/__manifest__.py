# -*- coding: utf-8 -*-
{
    'name': "kg_project_status_mail",

    'summary': """
        Send emails to users regarding project status""",

    'description': """
        Send emails to users regarding project status
    """,

    'author': "Mini K",
    'website': "http://www.klystronglobal.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Project',
    'version': '17.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base','project','mail','kg_project_milestone'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/project_configuration_form.xml',
        'views/project_project_stage_view.xml',
        'views/project_project_view.xml',
        'report/project_detail_pdf_report.xml',
        'report/project_detail_pdf_report_template.xml',
        'data/project_email_template.xml',
        'data/project_expiry_template.xml',
        'data/status_email_template.xml',
        'data/scheduler.xml',


    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
