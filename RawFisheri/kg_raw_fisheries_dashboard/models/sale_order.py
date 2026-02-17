# -*- coding: utf-8 -*-
from odoo import models, api
from datetime import datetime, timedelta


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def format_in_amount(self, value):
        if value is None:
            return "0.000"
        value = round(value, 3)
        return f"{value:,.3f}"

    @api.model
    def get_vessel_revenue_data(self):
        """ Function to load data for the vessel revenue dashboard """
        result = []
        vessels = self.env['sponsor.sponsor'].sudo().search([('is_vessel', '=', True)])
        today = datetime.today()
        first_day_of_this_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_day_of_previous_month = first_day_of_this_month - timedelta(seconds=1)
        first_day_of_previous_month = last_day_of_previous_month.replace(day=1, hour=0, minute=0, second=0,
                                                                         microsecond=0)
        for vessel in vessels:
            sale_orders = self.env['sale.order'].sudo().search([
                ('vessel_id', '=', vessel.id),
                ('state', '=', 'sale')
            ])
            prev_month_orders = sale_orders.filtered(
                lambda so: first_day_of_previous_month <= so.date_order <= last_day_of_previous_month
            )
            prev_month_revenue = sum(prev_month_orders.mapped('amount_total'))

            this_month_orders = sale_orders.filtered(
                lambda so: so.date_order >= first_day_of_this_month
            )
            this_month_revenue = sum(this_month_orders.mapped('amount_total'))

            total_revenue = sum(sale_orders.mapped('amount_total'))
            result.append({
                'vessel': vessel.name,
                'previous_month': self.format_in_amount(prev_month_revenue),
                'current_month': self.format_in_amount(this_month_revenue),
                'total_revenue': self.format_in_amount(total_revenue)
            })

        return result
