# -*- coding: utf-8 -*-
from odoo import models, api


class SaleDashboard(models.Model):
    """ This model is used to bring sale order datas, to show in sale dashboard """
    _name = 'sale.dashboard'
    _description = 'Sale Dashboard'

    @api.model
    def get_sale_data(self, domain):
        """ function to get sale order data and pass to js """
        data = self.env['sale.order'].search(domain)
        return data.read()