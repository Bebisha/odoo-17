# -*- coding: utf-8 -*-
from odoo import api, fields, models

class SurveySurveyLeads(models.Model):

    _inherit = "survey.survey"
    
    lead_survey = fields.Boolean(string="Lead Survey")
    partner_survey = fields.Boolean(string="Partner Survey")
    category_ids = fields.One2many('survey.category', 'survey_id', string="Categories")
    campaign_id = fields.Many2one('marketing.campaign', string="Marketing Campaign")
    
class SurveySurveyCategory(models.Model):

    _name = "survey.category"
    
    survey_id = fields.Many2one('survey.survey', string="Survey")
    name = fields.Char(string="Name")