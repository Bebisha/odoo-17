# -*- coding: utf-8 -*-
from odoo import api, fields, models

class SurveySurveyPartner(models.Model):

    _inherit = "res.partner"
    
    survey_ids = fields.One2many('survey.user_input', 'partner_id', string="Survey Answers")