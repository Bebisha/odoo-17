# -*- coding: utf-8 -*-

from odoo import models, fields, api


class FuelUsageAnalysis(models.Model):
    _name = 'fuel.usage.analysis'
    _description = 'fuel.usage.analysis'

    activity_id = fields.Many2one('budget.activity', string='Activity')
    vessel_id = fields.Many2one('sponsor.sponsor', string='Vessel')
    date = fields.Date(string='Date')
    tons_mgo = fields.Float(strng='Daily Use MGO(in Tons)')
    tons_hfo = fields.Float(strng='Daily Use HFO(in Tons)')
    production= fields.Float(string='Production')
