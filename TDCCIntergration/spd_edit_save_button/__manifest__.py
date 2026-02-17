{
    'name': 'Edit and Save Button in Odoo 17',
    'version': '17.0.1.0',
    'summary': 'Enable Edit, Save, and Discard Buttons in Odoo 17 Forms',
    'description': """
        This module introduces a streamlined way to manage records in Odoo 17 forms. 
        Users can easily switch between edit mode, save changes, or discard modifications 
        using intuitive buttons directly in the form view.
    """,
    'author': 'SPD Solutions Pvt. Ltd.',
    'company': 'SPD Solutions Pvt. Ltd.',
    'maintainer': 'SPD Solutions Pvt. Ltd.',
    'category': 'Tools',
    'depends': ['base'],
    'assets': {
        'web.assets_backend': [
            '/spd_edit_save_button/static/src/views/form/form_controller.xml',
            '/spd_edit_save_button/static/src/views/form/form_controller.js',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}

