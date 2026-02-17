{
    'name': "KG UAE SIF Report",

    "summary": "Customization for UAE SIF Report",
    "version": "17.0.1.0.0",
    'author': "Klystron Global",
    'maintainer': "SHARMI SV",
    "license": "OPL-1",
    'website': 'https://www.klystronglobal.com',
    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'hr_holidays', 'hr_payroll',
                'hr_attendance', 'hr_contract'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',

        'wizard/sif_report_wizard.xml',

        'views/res_company_views.xml',
        'views/res_bank_views.xml',
    ],

}
