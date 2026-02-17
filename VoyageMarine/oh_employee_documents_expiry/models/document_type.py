# -*- coding: utf-8 -*-
from odoo import models, fields


class DocumentType(models.Model):
    _name = 'document.type'

    name = fields.Char(string="Name", required=True, help="Name")
