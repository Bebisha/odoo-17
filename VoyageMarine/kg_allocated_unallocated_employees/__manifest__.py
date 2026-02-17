{
    'name': "Allocated Unallocated Employees",

    "summary": "Customization for Allocated Unallocated Employees",
    "version": "17.0.1.0.0",
    'author': "Klystron Global",
    'maintainer': "SHARMI SV",
    "license": "OPL-1",
    'website': 'https://www.klystronglobal.com',
    # any module necessary for this one to work correctly
    'depends': ['base', 'kg_voyage_marine_hrms', 'timesheet_grid', 'hr'],
    # always loaded  'kg_purchase', 'kg_voyage_marine_timesheet',,'ent_hr_gratuity_settlement'
    'data': [
        'security/ir.model.access.csv',

        'report/allocated_unallocated_emp_report.xml',
        'report/report.xml',

        'views/hr_employee_views.xml',

        'wizard/allocated_unallocated_employees_wizard.xml',
    ],

}
