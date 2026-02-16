{
    'name': 'KG HMS Developing Child Center',
    'version': '17.1.1',
    'summary': 'Handling the Frontend and Backend of Hospital Management System',
    'live_test_url': '',
    'author': 'Anal Joy',
    'company': 'Klystron Global',
    'website': 'https://www.klystronglobal.com',
    'depends': ['base', 'contacts', 'website'],
    'category': 'Hospital Management Services',
    'maintainer': 'Klystron Global',
    'data': ['security/ir.model.access.csv',
             'demo/form_sequence.xml',
             'views/dev_history.xml',
             'views/client_intake_form.xml',
             'views/dev_history_portal.xml',
             ],
    'assets': {
        'web.assets_frontend':
            [
                'kg_hms/static/src/css/developmental_form.css',
                'kg_hms/static/src/js/developmental_history.js',
            ], },
    'installable': True,
    'application': False,
    # 'auto_install': False,
    # 'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
}
