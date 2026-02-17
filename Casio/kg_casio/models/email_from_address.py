# -*- coding: utf-8 -*-
# from odoo.exceptions import Warning

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import timedelta, date
import random
import string

class Company(models.Model):
    _inherit = 'res.company'

    email_ids = fields.Many2many('email.from.address', 'email_company_rel', 'company_id', 'email_id', string='From Addresses')


class EmailFromAddress(models.Model):
    _name = 'email.from.address'
    _description='Email From Address'

    name = fields.Char('Name',required=True)
    email = fields.Char('Email',required=True)