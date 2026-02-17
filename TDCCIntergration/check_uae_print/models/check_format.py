# -*- coding: utf-8 -*-
from odoo import fields, models


class Check_Format(models.Model):
    _name = 'cheque.format'
    _description = 'Cheque Format'

    """ cheque """
    name = fields.Char("Cheque Format", required=True)
    top_margin = fields.Float("Top Margin", default=10)
    left_margin = fields.Float("Left Margin", default=10)
    """ cheque date """
    date_top_margin = fields.Float("Date Top Margin")
    date_left_margin = fields.Float("DateLeft Margin")
    date_font_size = fields.Float("Date Font Size", default=100)
    date_char_spacing = fields.Float("Date Charactor Spacing", default=1)
    """ payee name """
    payee_top_margin = fields.Float("Payee Top Margin")
    payee_left_margin = fields.Float("Payee Left Margin")
    payee_font_size = fields.Float("Payee Font Size", default=100)
    """ amount """
    amount_top_margin = fields.Float("Amount Top Margin")
    amount_left_margin = fields.Float("Amount Left Margin")
    amount_font_size = fields.Float("Amount Font Size", default=100)
    currency_symbol = fields.Boolean("Currency Symbol")
    dir_currency_symbol = fields.Selection(
        [('after', 'After'), ('before', 'Before')],
                                           string="Currency Symbol Position")
    """ amount in words """
    # 1st line
    amount_words1_top_margin = fields.Float("Amount Top Margin")
    amount_words1_left_margin = fields.Float("Amount Left Margin")
    amount_words1_font_size = fields.Float("Amount Font Size", default=100)
    amount_words1_width = fields.Float("Amount Width", default=100)
    # 2nd line
    amount_words2_top_margin = fields.Float("Amount Top Margin Words")
    amount_words2_left_margin = fields.Float("Amount Left Margin Words")
    amount_words2_font_size = fields.Float("Amount Font Size Words", default=100)
    amount_words2_width = fields.Float("Amount Width Words", default=100)

    _sql_constraints = [(
                        'name',
                        'unique (name)',
                        "Cheque Format already exists !")]
