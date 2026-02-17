import base64
from datetime import datetime

import xlsxwriter
from six import BytesIO

from odoo import fields, models, api
from odoo.exceptions import UserError


class KgActivity(models.Model):
    _name = 'kg.activity'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Activity'

    name = fields.Char()