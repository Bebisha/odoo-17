{
    'name': 'KG Push Notification',
    'version': '17.0.1.0.0',
    'category': 'KG Push Notification',
    'license': 'LGPL-3',
    'depends': [
        'project'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/push_notification_views.xml',
        'views/res_users_views.xml',
        'views/res_config_settings.xml',
    ],
    'installable': True,
}
