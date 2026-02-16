from odoo import models, fields


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    cheque_leaf_lines = fields.One2many('cheque.leaf.line', 'journal_id', string="Cheque Leaf Lines")
    cheque_series = fields.Char(string="Cheque Series")
    # name = fields.Char(string="Cheque Series")


