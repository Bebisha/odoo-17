# -*- coding: utf-8 -*-

from odoo import models, fields


class ProjectTaskType(models.Model):
    _inherit = 'project.project.stage'

    is_amc = fields.Boolean('Is AMC')
    is_closed = fields.Boolean('Is Closed')


