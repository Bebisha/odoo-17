from odoo import models, fields


class TransactionDocumentsType(models.Model):
    _name = "transaction.documents.type"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Transaction Documents Type"

    name = fields.Char(string="Name")