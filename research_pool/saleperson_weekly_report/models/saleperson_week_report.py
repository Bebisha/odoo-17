# -*- coding: utf-8 -*-
import base64
from datetime import timedelta, date
from datetime import datetime, timedelta
from io import BytesIO
import xlsxwriter

from odoo import fields, models, _,api
from odoo.exceptions import ValidationError

class SaleOrder(models.Model):

    _inherit = 'sale.order'

    # start_date = fields.Date(string='Start Date',default=lambda self: date.today() - timedelta(days=date.today().weekday()), store=True)
    # weekly_end_date = fields.Date(string='End Date', compute='_compute_dates', store=True)
    # monthly_end_date = fields.Date(string='End Date', compute='_compute_dates', store=True)

    @api.model
    def mail_monthly_sales_report(self):
        today = date.today()
        print(today)
        first_day = today.replace(day=1)
        print(first_day)
        last_day = (first_day + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        print(last_day)

        start_date = fields.Date.to_string(first_day)
        print(start_date)
        end_date = fields.Date.to_string(last_day)
        print(end_date)

        # Get sales orders for the month
        sales_orders = self.search([('date_order', '>=', start_date), ('date_order', '<=', end_date)])

        # Get recipients from configuration
        sales_report_recipients_param = self.env['ir.config_parameter'].sudo().get_param(
            'saleperson_weekly_report.sales_report_recipients', default='')
        print(sales_report_recipients_param,'sales_report_recipients_param')
        sales_report_recipients_ids = [int(id) for id in sales_report_recipients_param.split(',') if id.isdigit()]
        partners = self.env['res.partner'].browse(sales_report_recipients_ids)
        print('partners',partners)
        email_recipients = [partner.email for partner in partners if partner.email]
        print('email_recipients',email_recipients)
        if not email_recipients:
            raise UserError(_("No recipients found. Please choose recipients for the stock move report."))

        # Group sales orders by salesperson
        salesperson_sales = {}
        for order in sales_orders:
            salesperson = order.user_id
            if salesperson not in salesperson_sales:
                salesperson_sales[salesperson] = []
            salesperson_sales[salesperson].append(order)
        print(salesperson_sales,'salesperson_sales')

        # Create email content
        if not salesperson_sales:
            print('pppppppppppppppppp')
            for recipient in email_recipients:
                mail_content = (
                    f"Hello,<br>No sales records were found for the month from {start_date} to {end_date}."
                )
                subject = _('Monthly Sales Report - No Records')
                main_content = {
                    'subject': subject,
                    'author_id': self.env.user.partner_id.id,
                    'body_html': mail_content,
                    'email_to': recipient,
                }
                self.env['mail.mail'].create(main_content).send()
            return

        # Create tables for each salesperson
        overall_sales_table = '<h2>Monthly Sales Report</h2>'
        for salesperson, orders in salesperson_sales.items():
            sales_table = f'<h3>Sales Report for {salesperson.name}</h3>'
            sales_table += '<table border="1"><tr><th>Order Number</th><th>Customer</th><th>Total Amount</th><th>Order Date</th></tr>'
            for order in orders:
                sales_table += f'<tr><td>{order.name}</td><td>{order.partner_id.name}</td><td>{order.amount_total}</td><td>{order.date_order}</td></tr>'
            sales_table += '</table>'
            overall_sales_table += sales_table

        mail_content = (
            f"Hello,<br>Here is the sales report for the month from {start_date} to {end_date}:<br>{overall_sales_table}"
        )
        subject = _('Monthly Sales Report')

        report = self.env.ref('saleperson_weekly_report.report_monthly_sale')
        pdf_data = self.env['ir.actions.report'].sudo()._render_qweb_pdf(report, sales_orders.ids)[0]
        attachment = self.env['ir.attachment'].create({
            'name': 'Monthly_Sales_Report.pdf',
            'type': 'binary',
            'datas': base64.b64encode(pdf_data),
            'res_model': 'sale.order',
            'res_id': self.id,
            'mimetype': 'application/pdf'
        })

        # Send email to all recipients
        for recipient in email_recipients:
            print(recipient,'recipient')
            main_content = {
                'subject': subject,
                'author_id': self.env.user.partner_id.id,
                'body_html': mail_content,
                'email_to': recipient,
                'attachment_ids': [(6, 0, [attachment.id])],
            }
            print(main_content)
            self.env['mail.mail'].create(main_content).send()



    def get_salesperson_groups(self):
        groups = {}
        for order in self:
            salesperson = order.user_id.name
            if salesperson not in groups:
                groups[salesperson] = []
            groups[salesperson].append(order)
        print(groups,'groupsssssssssssssssss')
        return groups

    @api.model
    def mail_weekly_sales_report(self):
        start_date = fields.Date.to_string(date.today() - timedelta(days=date.today().weekday()))
        end_date = fields.Date.to_string(date.today() + timedelta(days=(6 - date.today().weekday())))
        print(end_date,'end_date')
        today = date.today()

        # Get sales orders for the week
        sales_orders = self.search([('date_order', '>=',start_date), ('date_order', '<=', end_date)])

        # Get recipients from configuration
        sales_report_recipients_param = self.env['ir.config_parameter'].sudo().get_param(
            'saleperson_weekly_report.sales_report_recipients', default='')
        sales_report_recipients_ids = [int(id) for id in sales_report_recipients_param.split(',') if id.isdigit()]
        partners = self.env['res.partner'].browse(sales_report_recipients_ids)
        email_recipients = [partner.email for partner in partners if partner.email]
        if not email_recipients:
            raise UserError(_("No recipients found. Please choose recipients for the stock move report."))

        # Group sales orders by salesperson
        salesperson_sales = {}
        for order in sales_orders:
            salesperson = order.user_id
            if salesperson not in salesperson_sales:
                salesperson_sales[salesperson] = []
            salesperson_sales[salesperson].append(order)

        # Create email content
        if not salesperson_sales:
            for recipient in email_recipients:
                mail_content = (
                    f"Hello,<br>No sales records were found for the week from {start_date} to {end_date}."
                )
                subject = _('Weekly Sales Report - No Records')
                main_content = {
                    'subject': subject,
                    'author_id': self.env.user.partner_id.id,
                    'body_html': mail_content,
                    'email_to': recipient,
                }
                self.env['mail.mail'].create(main_content).send()
            return

        # Create tables for each salesperson
        overall_sales_table = '<h2>Weekly Sales Report</h2>'
        for salesperson, orders in salesperson_sales.items():
            sales_table = f'<h3>Sales Report for {salesperson.name}</h3>'
            sales_table += '<table border="1"><tr><th>Order Number</th><th>Customer</th><th>Total Amount</th><th>Order Date</th></tr>'
            for order in orders:
                sales_table += f'<tr><td>{order.name}</td><td>{order.partner_id.name}</td><td>{order.amount_total}</td><td>{order.date_order}</td></tr>'
            sales_table += '</table>'
            overall_sales_table += sales_table

        mail_content = (
            f"Hello,<br>Here is the sales report for the week from {start_date} to {end_date}:<br>{overall_sales_table}"
        )
        subject = _('Weekly Sales Report')

        # Generate the PDF report
        report = self.env.ref('saleperson_weekly_report.report_weekly_sale')
        pdf_data = self.env['ir.actions.report'].sudo()._render_qweb_pdf(report, sales_orders.ids)[0]
        attachment = self.env['ir.attachment'].create({
            'name': 'Weekly_Sales_Report.pdf',
            'type': 'binary',
            'datas': base64.b64encode(pdf_data),
            'res_model': 'sale.order',
            'res_id': self.id,
            'mimetype': 'application/pdf'
        })

        # Send email to all recipients with the PDF attachment
        for recipient in email_recipients:
            main_content = {
                'subject': subject,
                'author_id': self.env.user.partner_id.id,
                'body_html': mail_content,
                'email_to': recipient,
                'attachment_ids': [(6, 0, [attachment.id])],
            }
            self.env['mail.mail'].create(main_content).send()






