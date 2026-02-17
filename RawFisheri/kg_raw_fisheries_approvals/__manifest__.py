{
    'name': "KG Raw Fisheries Approvals",

    "summary": "Customization for Approvals Module",
    "version": "17.0.1.0.0",
    'category': 'Approvals',
    'author': "Klystron Global",
    'maintainer': "SHARMI SV",
    "license": "OPL-1",
    'website': 'https://www.klystronglobal.com',
    'depends': ['base', 'account', 'approvals'],
    'data': [
        'security/res_groups.xml',

        'data/approval_type.xml',

        'views/approval_request_views.xml',
    ],
}
