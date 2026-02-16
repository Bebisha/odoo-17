# -*- coding: utf-8 -*-

from odoo import models, fields, _


class KgChequeLayout(models.Model):
    _name = 'kg.cheque.layout'
    _description = 'Kg Cheque Layout'

    name = fields.Char('Name', required=True)

    # Header info
    header_height = fields.Float('Height', default=4, store=True)
    header_width = fields.Float('Width', default=19.8, store=True)
    table_margin = fields.Float('Margin Top', default=0, store=True)
    table_margin_left = fields.Float('Margin Left', default=0, store=True)
    table_margin_right = fields.Float('Margin Right', default=0, store=True)
    table_margin_bottom = fields.Float('Margin Bottom', default=0, store=True)

    font_size = fields.Float('Font Size', default=14, store=True)
    font_bold = fields.Boolean('Font Bold', default=False, store=True)

    header_font_size = fields.Float(string="Header Font Size")
    bank_name_div_left = fields.Float(string="Bank Name Margin Left")
    bank_name_div_top = fields.Float(string="Bank Name Margin Top")
    payment_ref_left = fields.Float(string="Payment Ref Left")
    payee_name_left = fields.Float(string="Payee Name Left")
    payment_date_left = fields.Float(string="Payment Date Left")
    cheque_trans_date_left = fields.Float(sttring="Transaction Date Left")
    header_amount_left = fields.Float(string="Amount Left")
    currency_left = fields.Float(string="Currency Left")


    # Accounting info
    a_margin_top = fields.Float('Acc Margin Top', default=0, store=True)
    a_margin_left = fields.Float('Acc Margin Left', default=0, store=True)
    a_margin_right = fields.Float('Acc Margin Right', default=0, store=True)
    a_margin_bottom = fields.Float('Acc Margin Bottom', default=0, store=True)
    row_height = fields.Float('Row Height', default=0.8, store=True)
    a_height = fields.Float('Accounting Info Height', default=1, store=True)
    label_width = fields.Float('Label Width', default=4, store=True)
    slabel_width = fields.Float('Second Label Width', default=3, store=True)
    fcolumn_width = fields.Float('First Col Width', default=19.9, store=True)
    scolumn_width = fields.Float('Second Col Width', default=7.8, store=True)
    # Payment info
    p_margin_top = fields.Float('Payment Margin Top', default=0, store=True)
    p_margin_left = fields.Float('Payment Margin Left', default=0, store=True)
    p_margin_right = fields.Float('Payment Margin Right', default=0, store=True)
    p_margin_bottom = fields.Float('Payment Margin Bottom', default=0, store=True)
    prow_height = fields.Float('Row Height', default=0.8, store=True)
    psrow_height = fields.Float('Second Row Height', default=6, store=True)
    col1_width = fields.Float('Col1 Width', default=2.1, store=True)
    col2_width = fields.Float('Col2 Width', default=2.1, store=True)
    col3_width = fields.Float('Col3 Width', default=7.7, store=True)
    col4_width = fields.Float('Col4 Width', default=3.8, store=True)
    col5_width = fields.Float('Col5 Width', default=3.9, store=True)
    # Amount info
    amount_row_height = fields.Float('Amt Row Height', default=0.8, store=True)
    amount_row_margin_top = fields.Float('Amt Row Margin Top', default=0, store=True)
    amount_row_margin_left = fields.Float('Amt Row Margin Left', default=0, store=True)
    amount_row_margin_right = fields.Float('Amt Row Margin Right', default=0, store=True)
    amount_row_margin_bottom = fields.Float('Amt Row Margin Bottom', default=0, store=True)
    # Signature info
    sig_row_height = fields.Float('Row Height', default=3.9, store=True)
    # Cheque info
    chequeno_top = fields.Float('Cheque No Top', default=2.6, store=True)
    chequeno_left = fields.Float('Cheque No Left', default=2.6, store=True)
    date_top = fields.Float('Date Top', default=2.6, store=True)
    date_left = fields.Float('Date Left', default=19, store=True)
    payee_top = fields.Float('Payee Top', default=3.5, store=True)
    payee_left = fields.Float('Payee Left', default=2.6, store=True)
    word_top = fields.Float('Amount in Words-Top', default=4.4, store=True)
    word_left = fields.Float('Amount in Words-Left', default=2.6, store=True)
    amount_top = fields.Float('Amount Top', default=4.6, store=True)
    amount_left = fields.Float('Amount Left', default=22, store=True)

