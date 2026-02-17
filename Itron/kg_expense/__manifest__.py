{
    "name": 'KG Expense',
    "version": '17.0.1.0.0',
    'license': 'LGPL-3',
    'author': "Klystron Global",
    'website': "http://www.klystronglobal.com",
    'depends': [
        'base','mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/expense_data.xml',
        'views/kg_expense_category.xml',
        'views/kg_expense_views.xml',
    ],
    "installable": True,
}
