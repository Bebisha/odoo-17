# Ashish Thomas
{
    "name": "Kg Cheque Layout",
    "summary": "Set Layout for Cheque",
    "version": "17.0.1.0.0",
    'category': 'Accounting/Accounting',
    "author": "Klystron Global",
    "license": "AGPL-3",
    "depends": ["account_check_printing", "base", 'account'],
    "data": [
        'security/ir.model.access.csv',
        'reports/cheque_payment_temp.xml',

        'views/cheque_layout_view.xml',
        # 'views/journal_views.xml',
        'views/account_journal_views.xml',
        'views/account_move_line.xml',
        'views/account_payment_views.xml',
        'views/cheque_leaf_views.xml',
        'wizard/generate_cheque_wizard.xml',
        'wizard/update_payment_cheque_wizard.xml',
             ],
    "installable": True,
}
