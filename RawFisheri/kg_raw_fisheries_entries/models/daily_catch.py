# -*- coding: utf-8 -*-

from odoo import models, fields, api


class DailyCatch(models.Model):
    _name = 'daily.catch'
    _description = 'daily.catch'

    # name = fields.Char(string='Description')
    date = fields.Date(string='Date', required=True)
    vessel_id = fields.Many2one('sponsor.sponsor', string='Vessel')
    activity_id = fields.Many2one('budget.activity', string='Activity')
    total_on_board = fields.Float(string='Total On Board')
    catch_of_day = fields.Float(string='Catch Of The Day', compute='_compute_catch_of_day', readonly=False, Store=True)
    country_id = fields.Many2one('res.country', string='Region')
    army = fields.Float(strng='Army')
    correction = fields.Float(strng='Correction')
    inventory = fields.Float(string='Inventory', compute='_compute_inventory', readonly=False)

    @api.depends('total_on_board')
    def _compute_inventory(self):
        """ Function to compute the value of inventory for Mauritania """
        for entry in self:
            if entry.country_id.code == 'MR':
                inventory = entry.total_on_board * 0.97
                entry.write({
                    'inventory': inventory,
                })
            else:
                entry.write({
                    'inventory': 0.0,
                })

    @api.depends('date', 'total_on_board')
    def _compute_catch_of_day(self):
        """ Function to compute value of catch for the day """
        for entry in self:
            if entry.date and entry.total_on_board:
                prev_day_data = self.env['daily.catch'].search([
                    ('date', '<', entry.date), ('vessel_id', '=', entry.vessel_id.id),
                    ('date', '>=', entry.date.replace(day=1))
                     ], order='date desc', limit=1)
                if prev_day_data:
                    entry.catch_of_day = entry.total_on_board - prev_day_data.total_on_board
                else:
                    entry.catch_of_day = 0.0
            else:
                entry.catch_of_day = 0.0
