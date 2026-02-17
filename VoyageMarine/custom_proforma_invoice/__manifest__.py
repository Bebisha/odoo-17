{
    'name': 'Custom Proforma Invoice',
    'version': '17.0.1.0.0',
    'summary': 'Custom Proforma Invoice similar to BI Proforma',
    'category': 'Sales',
    'author': 'Custom',
    'depends': ['sale', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/proforma_views.xml',
        'views/sale_order_inherit.xml',
        'report/sale_proforma_invoice_report.xml',
        'report/proforma_report.xml',
        'report/templates.xml',
        'data/email_template_data.xml',
    ],
    'installable': True,
    'application': False,
}