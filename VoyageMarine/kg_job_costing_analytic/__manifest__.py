{
    'name': 'Job Costing (Analytic Based)',
    'version': '17.0.1.0.0',
    'category': 'Sales',
    'summary': 'Analytic based Job Costing from Sale Order',
    'depends': ['sale', 'account', 'analytic', 'hr_expense', 'sale_expense'],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/expense_view.xml',
        'wizard/job_costing_wizard_view.xml',
        'report/job_costing_report_template.xml',
        'report/job_costing_report.xml',

    ],
    'installable': True,
    'application': False,
}
