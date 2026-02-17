# -*- coding: utf-8 -*-

from odoo import fields, models, _, api


class StockQuant(models.Model):
    _inherit = "stock.quant"

    def get_stock_count(self):
        valuation_data = []
        requests = self.env['stock.quant'].sudo().search([('inventory_date', '!=', False)])
        for req in requests:
            formatted_date = req.inventory_date.strftime('%d/%m/%Y') if req.inventory_date else ''

            valuation_data.append({
                'id': req.id,
                'product_id': req.product_id.name,
                'reference': req.product_id.default_code,
                'company': req.company_id.name,
                'company_id': req.company_id.id,
                'uom': req.product_uom_id.name,
                'inventory_date': formatted_date,
                'quantity': req.quantity,

            })

        company_data = []
        companies = self.env.user.sudo().company_ids

        for company in companies:
            company_data.append({
                'id': company.id,
                'name': company.name,
                'country_code': company.country_id.code if company.country_id else '',
            })

        return {
            'requests': valuation_data,
            'companies': company_data,
        }
