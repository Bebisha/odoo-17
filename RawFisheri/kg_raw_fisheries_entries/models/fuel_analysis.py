# -*- coding: utf-8 -*-

from odoo import models, fields, api


class FuelAnalysis(models.Model):
    _name = 'fuel.analysis'
    _description = 'fuel.analysis'

    name = fields.Char(string='Description')
    date = fields.Date(string='Date')
    vessel_id = fields.Many2one('sponsor.sponsor', string='Vessel')
    tons_mgo = fields.Float(strng='Quantity MGO(in Tons)')
    tons_hfo = fields.Float(strng='Quantity HFO(in Tons)')
    usd_mgo = fields.Float(strng='Price MGO')
    usd_hfo = fields.Float(strng='Price HFO')
    price_avg_mgo = fields.Float(strng='Price MGO(Average)', compute='_compute_price_average')
    price_avg_hfo = fields.Float(strng='Price HFO(Average)', compute='_compute_price_average')

    @api.depends('tons_mgo', 'tons_hfo', 'usd_mgo', 'usd_hfo')
    def _compute_price_average(self):
        """ Function to compute the price average for mgo and hfo """
        for rec in self:
            if rec.usd_mgo and rec.tons_mgo:
                price_avg_mgo = rec.usd_mgo / rec.tons_mgo
                rec.write({
                    'price_avg_mgo': price_avg_mgo,
                })
            else:
                rec.price_avg_mgo = 0.0
            if rec.usd_hfo and rec.tons_hfo:
                price_avg_hfo = rec.usd_hfo / rec.tons_hfo
                rec.write({
                    'price_avg_hfo': price_avg_hfo,
                })
            else:
                rec.price_avg_hfo = 0.0