# -*- coding: utf-8 -*-
from odoo import models, fields


class KgEmiratesId(models.Model):
    _name = 'kg.emiratesid.scan'
    _description = 'Emirates ID Records'

    name = fields.Char('Name')
    machine_id = fields.Char('Machine Id')
    data = fields.Text('Data')
    user_id = fields.Many2one('res.users', 'User')
