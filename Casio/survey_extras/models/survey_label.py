# -*- coding: utf-8 -*-
from odoo import api, fields, models

class SurveyLabelConditional(models.Model):

    _inherit = "survey.question.answer"
    
    conditional_question_ids = fields.One2many('survey.question','conditional_option_id', string="Conditionals Questions")
    category_ids = fields.One2many('survey.label.category', 'label_id', string="Categories")
    
class SurveyLabelCategory(models.Model):

    _name = "survey.label.category"
    
    label_id = fields.Many2one('survey.question.answer', string="Survey Label")
    category_id = fields.Many2one('survey.category', required="True", string="Category")
    points = fields.Integer(string="Points")