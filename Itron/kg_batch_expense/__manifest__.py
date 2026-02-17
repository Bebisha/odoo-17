{
    "name": 'KG Batch Expense',
    "version": '17.0.1.0.0',
    'license': 'LGPL-3',
    'author': "Klystron Global",
    'website': "http://www.klystronglobal.com",
    'depends': [
        'base','mail','hr','hr_expense',
    ],
    'data': [
        'data/server_action_expense.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'views/hr_expense.xml',
        'views/kg_main_catergory.xml',
        'views/settings.xml',
        'wizard/payment_expense_wizard.xml',
    ],
    "installable": True,
}
