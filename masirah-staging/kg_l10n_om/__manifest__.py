{
    'name': 'KG Oman Vat Report',
    'version': '17.0.1.0.0',
    'summary': """KG Oman Vat Report""",
    'description': """KG Oman Vat Report""",
    'author': 'Klystron Global',
    'maintainer': 'Binu A R',
    'website': "https://www.klystronglobal.com/",
    'images': ["static/description/banner.png"],
    'license': 'AGPL-3',
    'category': 'Accounting',
    'sequence': 1,
    'depends': ['base', 'account','account_accountant'],
    'data': [
        'data/account_tax_report.xml',
        'data/template/account.tax.group-om.csv',
        # 'data/template/account.tax-om.csv',
        'data/account_tax_data.xml',

    ],
    'installable': True,

}
