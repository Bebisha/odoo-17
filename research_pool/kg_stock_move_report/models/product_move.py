# -*- coding: utf-8 -*-
import base64
from datetime import timedelta, date
from datetime import datetime, timedelta
from odoo.exceptions import UserError
from io import BytesIO
import xlsxwriter

from odoo import fields, models, _,api
from odoo.exceptions import ValidationError

class StockMove(models.Model):

    _inherit = 'stock.move'


    def get_product_groups(self):
        product_groups = {}
        for move in self:
            product = move.product_id.name
            if product not in product_groups:
                product_groups[product] = []
            product_groups[product].append(move)
        print(product_groups, 'product groups')
        return product_groups

    @api.model
    def mail_monthly_stock_move_report(self):
        print("jjjjjjjjjjjj")
        today = date.today()
        first_day = today.replace(day=1)
        last_day = (first_day + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        start_date = fields.Date.to_string(first_day)
        end_date = fields.Date.to_string(last_day)

        # Get stock moves for the last month
        stock_moves = self.env['stock.move'].search([('date', '>=', start_date), ('date', '<=', end_date)])
        print('stock_moves',stock_moves)

        # Get recipients from configuration
        stock_report_recipients_param = self.env['ir.config_parameter'].sudo().get_param(
            'kg_stock_move_report.stock_recipient_id', default='')
        stock_report_recipients_ids = [int(id) for id in stock_report_recipients_param.split(',') if id.isdigit()]
        partners = self.env['res.partner'].browse(stock_report_recipients_ids)
        email_recipients = [partner.email for partner in partners if partner.email]
        print(email_recipients,'email_recipients')
        if not email_recipients:
            raise UserError(_("No recipients found. Please choose recipients for the stock move report."))

        # Group stock moves by product
        product_moves = {}
        for move in stock_moves:
            product = move.product_id
            if product not in product_moves:
                product_moves[product] = []
            product_moves[product].append(move)

        # Create email content
        if not product_moves:
            print(product_moves,'product_moves')
            for recipient in email_recipients:
                mail_content = (
                    f"Hello,<br>No stock moves were found for the month from {start_date} to {end_date}."
                )
                subject = _('Monthly Stock Move Report - No Records')
                main_content = {
                    'subject': subject,
                    'author_id': self.env.user.partner_id.id,
                    'body_html': mail_content,
                    'email_to': recipient,
                }
                self.env['mail.mail'].create(main_content).send()
            return

        # Create tables for each product
        overall_moves_table = '<h2>Monthly Stock Move Report</h2>'
        for product, moves in product_moves.items():
            moves_table = f'<h3>Stock Move Report for {product.name}</h3>'
            moves_table += '<table border="1"><tr><th>Move Reference</th><th>Source Location</th><th>Destination Location</th><th>Quantity</th><th>Remaining Quantity</th><th>Move Date</th></tr>'
            for move in moves:
                remaining_qty = move.product_id.qty_available - move.product_uom_qty
                moves_table += f'<tr><td>{move.name}</td><td>{move.location_id.name}</td><td>{move.location_dest_id.name}</td><td>{move.product_uom_qty}</td><td>{remaining_qty}</td><td>{move.date}</td></tr>'
            moves_table += '</table>'
            overall_moves_table += moves_table

        mail_content = (
            f"Hello,<br>Here is the stock move report for the month from {start_date} to {end_date}:<br>{overall_moves_table}"
        )
        subject = _('Monthly Stock Move Report')

        report = self.env.ref('kg_stock_move_report.report_monthly_stock')
        pdf_data = self.env['ir.actions.report'].sudo()._render_qweb_pdf(report, stock_moves.ids)[0]
        attachment = self.env['ir.attachment'].create({
            'name': 'Monthly_Stock_Move_Report.pdf',
            'type': 'binary',
            'datas': base64.b64encode(pdf_data),
            'res_model': 'stock.move',
            'res_id': self.id,
            'mimetype': 'application/pdf'
        })

        # Send email to all recipients
        for recipient in email_recipients:
            main_content = {
                'subject': subject,
                'author_id': self.env.user.partner_id.id,
                'body_html': mail_content,
                'email_to': recipient,
                'attachment_ids': [(6, 0, [attachment.id])],
            }
            print(main_content,'main_content')
            self.env['mail.mail'].create(main_content).send()

    @api.model
    def mail_weekly_stock_report(self):
        start_date = fields.Date.to_string(date.today() - timedelta(days=date.today().weekday()))
        end_date = fields.Date.to_string(date.today() + timedelta(days=(6 - date.today().weekday())))
        print(end_date, 'end_date')

        # Get stock moves for the week
        stock_moves = self.env['stock.move'].search([('date', '>=', start_date), ('date', '<=', end_date)])
        print('stock_moves', stock_moves)

        # Get recipients from configuration
        stock_report_recipients_param = self.env['ir.config_parameter'].sudo().get_param(
            'kg_stock_move_report.stock_recipient_id', default='')
        stock_report_recipients_ids = [int(id) for id in stock_report_recipients_param.split(',') if id.isdigit()]
        partners = self.env['res.partner'].browse(stock_report_recipients_ids)
        email_recipients = [partner.email for partner in partners if partner.email]
        print(email_recipients, 'email_recipients')
        if not email_recipients:
            raise UserError(_("No recipients found. Please choose recipients for the stock move report."))

        # Group stock moves by product
        product_moves = {}
        for move in stock_moves:
            product = move.product_id
            if product not in product_moves:
                product_moves[product] = []
            product_moves[product].append(move)

        # Create email content
        if not product_moves:
            print(product_moves, 'product_moves')
            for recipient in email_recipients:
                mail_content = (
                    f"Hello,<br>No stock moves were found for the week from {start_date} to {end_date}."
                )
                subject = _('Weekly Stock Move Report - No Records')
                main_content = {
                    'subject': subject,
                    'author_id': self.env.user.partner_id.id,
                    'body_html': mail_content,
                    'email_to': recipient,
                }
                self.env['mail.mail'].create(main_content).send()
            return

        # Create tables for each product
        overall_moves_table = '<h2>Weekly Stock Move Report</h2>'
        for product, moves in product_moves.items():
            moves_table = f'<h3>Stock Move Report for {product.name}</h3>'
            moves_table += '<table border="1"><tr><th>Move Reference</th><th>Source Location</th><th>Destination Location</th><th>Quantity</th><th>Remaining Quantity</th><th>Move Date</th></tr>'
            for move in moves:
                remaining_qty = move.product_id.qty_available - move.product_uom_qty
                moves_table += f'<tr><td>{move.name}</td><td>{move.location_id.name}</td><td>{move.location_dest_id.name}</td><td>{move.product_uom_qty}</td><td>{remaining_qty}</td><td>{move.date}</td></tr>'
            moves_table += '</table>'
            overall_moves_table += moves_table

        mail_content = (
            f"Hello,<br>Here is the stock move report for the week from {start_date} to {end_date}:<br>{overall_moves_table}"
        )
        subject = _('Weekly Stock Move Report')

        report = self.env.ref('kg_stock_move_report.report_weekly_stock')
        pdf_data = self.env['ir.actions.report'].sudo()._render_qweb_pdf(report, stock_moves.ids)[0]
        attachment = self.env['ir.attachment'].create({
            'name': 'Weekly_Stock_Move_Report.pdf',
            'type': 'binary',
            'datas': base64.b64encode(pdf_data),
            'res_model': 'stock.move',
            'res_id': self.id,
            'mimetype': 'application/pdf'
        })

        # Send email to all recipients
        for recipient in email_recipients:
            main_content = {
                'subject': subject,
                'author_id': self.env.user.partner_id.id,
                'body_html': mail_content,
                'email_to': recipient,
                'attachment_ids': [(6, 0, [attachment.id])],
            }
            print(main_content, 'main_content')
            self.env['mail.mail'].create(main_content).send()
