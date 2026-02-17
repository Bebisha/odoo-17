# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class DailyStockReport(models.Model):
    _name = 'daily.stock'
    _description = 'daily.stock'

    name = fields.Char(string='Reference', default='New', readonly=True)
    date = fields.Date(string='Date')
    catch_of_day = fields.Float(string='Catch of the Day')
    vessel_id = fields.Many2one('sponsor.sponsor',string='Vessel')
    daily_stock_line_ids = fields.One2many('daily.stock.line','daily_stock_id', string='Lines')

    @api.model
    def create(self, vals):
        """ Daily stock sequence number generation """
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'daily.stock.sequence') or _('New')
        return super(DailyStockReport, self).create(vals)

class DailyStockReportLine(models.Model):
    _name = 'daily.stock.line'
    _description = 'daily.stock.line'

    product_category_id = fields.Many2one('product.category', string='Product')
    quantity = fields.Float(string='Quantity')
    daily_stock_id = fields.Many2one('daily.stock', string='Daily Stock')
