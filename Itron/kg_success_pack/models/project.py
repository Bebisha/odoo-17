# -*- coding: utf-8 -*-
from collections import defaultdict

from odoo import fields, models, _, api
from odoo.exceptions import UserError
from ast import literal_eval


class ProjectProject(models.Model):
    _inherit = "project.project"

    active_success_pack = fields.Boolean(string='Success Pack')
    success_pack_line_ids = fields.One2many('kg.success.pack.line', 'project_id', string='Success Pack Lines')
