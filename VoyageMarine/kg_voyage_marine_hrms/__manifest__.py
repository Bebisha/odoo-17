{
    'name': "KG Voyage Marine HRMS",

    "summary": "Customization for HRMS related Modules",
    "version": "17.0.1.0.0",
    'author': "Klystron Global",
    'maintainer': "SHARMI SV",
    "license": "OPL-1",
    'website': 'https://www.klystronglobal.com',
    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'hr_holidays', 'hr_payroll', 'documents', 'documents_hr', 'mail', 'account',
                'hr_contract_reports', 'kg_purchase', 'kg_voyage_marine_timesheet',
                'hr_attendance', 'hr_contract', 'hr_expense', 'l10n_ae_hr_payroll', 'hr_expense',
                'ent_hr_gratuity_settlement'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',

        'data/salary_rule.xml',
        'data/input_type.xml',
        'data/mail_template.xml',

        'views/hr_employee_entry_views.xml',
        'views/hr_employee_views.xml',
        'views/hr_payslip_views.xml',
        'views/hr_contract_views.xml',
        'views/hr_job_views.xml',
        'views/visa_designation_views.xml',
        'views/hr_attendance_views.xml',

        'wizard/salary_report_wizard.xml',
        'wizard/generate_employee_entries_wizard.xml',

        'report/report_payslip_tmp_inherit.xml',
'report/report.xml',
        'report/hr_gratuity_template.xml',

    ],

    'assets': {
        'web.assets_backend': [
            'kg_voyage_marine_hrms/static/src/xml/views/**/*',
            'kg_voyage_marine_hrms/static/src/js/**/*',
        ],
    }

}
