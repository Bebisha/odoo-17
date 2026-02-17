# -*- coding: utf-8 -*-
from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)
import base64

class SurveyQuestionConditional(models.Model):

    _inherit = "survey.question"
    
    conditional = fields.Boolean(string="Conditional")
    conditional_question_id = fields.Many2one('survey.question', string="Condition Question", help="The question which determines if this question is shown")
    conditional_option_id = fields.Many2one('survey.question.answer', string="Condition Option", help="The option which determines if this question is shown")
    question_type = fields.Selection(selection_add=[('binary', 'File Attachment')])

    # for pattern in odoo standard textbox
    validation_is_sh_textbox_pattern = fields.Boolean('Input must be in specified pattern')
    validation_sh_textbox_pattern = fields.Char('Textbox Pattern')
    validation_sh_textbox_placeholder = fields.Char('Textbox Placeholder')
    

    def validate_binary(self, post, answer_tag):
        self.ensure_one()
        errors = {}
        answer = post[answer_tag]
        # Empty answer to mandatory question
        if self.constr_mandatory and not answer:
            errors.update({answer_tag: self.constr_error_msg})
        # Email format validation
        # Note: this validation is very basic:
        #     all the strings of the form
        #     <something>@<anything>.<extension>
        #     will be accepted
        return errors
