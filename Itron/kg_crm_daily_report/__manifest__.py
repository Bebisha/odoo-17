{
    "name": 'Sales Daily Reporting',
    "version": '17.0.1.0.0',
    "installable": True,
    'author': "Klystron Global",
    'depends': [
        'base', 'kg_crm'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/crm_daily_report_views.xml',
        'views/mail_activity_type_views.xml',
        'views/res_config_settings.xml',
    ],
    'demo': [],
}
