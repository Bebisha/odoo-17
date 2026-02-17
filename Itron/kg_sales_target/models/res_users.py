# -*- coding: utf-8 -*-
import json

from odoo import fields, models, _


class ResUsers(models.Model):
    _inherit = "res.users"

    is_salesperson = fields.Boolean(string='Is Salesperson')

