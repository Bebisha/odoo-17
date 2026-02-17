# -*- coding: utf-8 -*-
from odoo import models, fields, api


class SurveyQuestionInh(models.Model):
    _inherit = 'survey.question'

    parent_id = fields.Many2one('survey.question', string="Parent Question",
                                help="Select the parent question to get the questions  related to that.")

    is_onchange = fields.Boolean(string='Make Onchange')
    model_id = fields.Many2one('ir.model','Master Model')
    model_field_id = fields.Many2one('ir.model.fields','Master Model Field')
