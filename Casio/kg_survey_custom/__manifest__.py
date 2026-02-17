{
    'name': 'Survey Custom',
    'version': '17.0.1.0.0',
    'author': '',
    'website': '',
    'description': """ """,
    'depends': ['base', 'survey'],
    'category': 'Survey',
    'data': [
         'security/ir.model.access.csv',
         'views/survey_template.xml',
         'views/survey_invite_view.xml',
         'views/survey_user_input.xml',
         'views/survey_survey_view.xml',

    ],
    'qweb': [],
    'demo': [
        ],
    'assets': {
        'survey.survey_assets': [
            ('include', "web.chartjs_lib"),

            'kg_survey_custom/static/src/js/survey_form.js',
        ],
    },
    'application': True,
    'license': 'OPL-1',
    'price': 299,
    'currency': 'EUR',
    'installable': True,
}
