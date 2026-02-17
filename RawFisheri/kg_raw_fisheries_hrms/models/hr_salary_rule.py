# -*- coding:utf-8 -*-

from odoo import models, fields, api


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    for_oman = fields.Boolean(string='For Omani')
