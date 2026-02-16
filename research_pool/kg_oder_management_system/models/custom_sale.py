import calendar
import json

from odoo import models, fields, api
from collections import defaultdict
from datetime import datetime, timedelta
import random


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def fetch_sales_data(self):
        confirmed_orders = self.env['sale.order'].search([('state', '=', 'sale')])
        total_amount = sum(order.amount_total for order in confirmed_orders)

        return total_amount

    @api.model
    def calculate_last_week_sales_amount(self):
        end_date = fields.Date.today()
        start_date = end_date - timedelta(days=7)

        last_week_sales_orders = self.search([
            ('date_order', '>=', start_date),
            ('date_order', '<=', end_date),
            ('state', '=', 'sale')
        ])

        last_week_sales_amount = sum(order.amount_total for order in last_week_sales_orders)
        print("hhhhhhh", last_week_sales_amount)
        return last_week_sales_amount

    @api.model
    def calculate_last_month_sales_amount(self):
        end_date = fields.Date.today()
        start_date = end_date.replace(day=1) - timedelta(days=1)

        last_month_sales_orders = self.search([
            ('date_order', '>=', start_date),
            ('date_order', '<=', end_date),
            ('state', '=', 'sale')
        ])

        last_month_sales_amount = sum(order.amount_total for order in last_month_sales_orders)
        print("last_month_sales_amount", last_month_sales_amount)
        return last_month_sales_amount

    @api.model
    def calculate_last_year_sales_amount(self):
        end_date = fields.Date.today()
        start_date = end_date.replace(year=end_date.year - 1)

        last_year_sales_orders = self.search([
            ('date_order', '>=', start_date),
            ('date_order', '<=', end_date),
            ('state', '=', 'sale')
        ])

        # Calculate the total sales amount for last year
        last_year_sales_amount = sum(order.amount_total for order in last_year_sales_orders)
        print("last_year_sales_amount", last_year_sales_amount)
        return last_year_sales_amount

    @api.model
    def get_sales_data(self):
        sales_data = []
        sales_orders = self.env['sale.order'].search([])
        for order in sales_orders:
            sales_data.append({
                'date': order.date_order,
                'amount_total': order.amount_total,

            })

            print('kkkkkkk', sales_data)
        return sales_data
