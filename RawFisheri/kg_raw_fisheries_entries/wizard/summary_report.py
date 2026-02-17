# -*- coding: utf-8 -*-

import io
from io import BytesIO
import base64
from datetime import datetime
import xlsxwriter
import xlwt

from odoo import models, fields, api
from odoo.exceptions import UserError


class ProductionReportWizard(models.TransientModel):
    _name = 'production.report.wizard'
    _description = 'production.report.wizard'

    date = fields.Date(string='Date')
    vessel_id = fields.Many2one('sponsor.sponsor')