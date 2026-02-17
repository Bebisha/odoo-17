{
    "name": "Customer Data API",
    "version": "1.2.1",
    "category": "API",
    'license': 'AGPL-3',
    "author": "Sumayya",
    "website": "www.klystronglobal.com",
    "summary": "Customer Data API",
    "description": """Common connector for external API requests.""",
    "depends": ["base", "crm", 'portal','web'],
    "data": [
        'views/res_config_settings.xml',
        # 'views/portal_templates.xml',
    ],
    "license": "LGPL-3",
    "installable": True,
    "auto_install": False,
}
