##############################################################################
#
#  Bista Solutions Inc.
#  Website: https://www.bistasolutions.com
#
##############################################################################
{
    'name': 'Account Followup Reports Extension',
    'version': '17.1.1',
    'license': 'LGPL-3',
    'sequence': 17,
    'category': 'Accounting',
    'summary': 'Follow up with invoice attachment',
    'description': """This modules extends the functionality of Account
    Follow-up Report module to add invoice attachment for selected invoices
    when sending email for follow-up.
    """,
    'author': 'Bista Solutions',
    'website': 'http://www.bistasolutions.com',
    'depends': ['account_reports', 'bista_tdcc_reports'],
    'data': [],
    'installable': True,
    'application': True,
}
