{
    'name': 'Kg GIT',
    'version': '17.0.1.0.0',
    'summary': 'Customizations for employee',
    'sequence': 100,
    'description': 'This module enhances employee functionalities.',
    'author': 'Klystron Global',
    'maintainer': 'Bebisha CP',
    'license': 'LGPL-3',

    'depends': ['base', 'purchase', 'sale', 'sale_management', 'stock', 'account', 'account_accountant','sale_stock'],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        # 'views/goods_in_transit.xml',
        'views/shipment_advice_views.xml',

        'views/stock.xml',
        'views/purchase_order_views.xml',

        'views/res_company.xml',
        'wizard/autopopulate_wizard.xml',
        'wizard/update_qty_wizard_views.xml',
        'views/boe_report.xml',
        'views/porduct_group.xml',
        'views/shipment_advise_summary_lines.xml',


        'wizard/boe_wizard.xml'


    ],
    'installable': True,
    'application': True,
}
