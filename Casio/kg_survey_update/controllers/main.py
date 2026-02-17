import json
import logging
import textwrap

import werkzeug
from datetime import datetime, timedelta
from math import ceil
from odoo import _
from dateutil.relativedelta import relativedelta

from odoo import fields, http, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.http import request
from odoo.tools import ustr
from odoo.addons.survey.controllers import main
_logger = logging.getLogger(__name__)


class SurveyController(main.Survey):

    def _prepare_survey_finished_values(self, survey, answer, token=False):
        result = super(SurveyController, self)._prepare_survey_finished_values(survey, answer, token)
        upt_qstn_lines = answer.user_input_line_ids.filtered(lambda x: x.question_id.update_result)
        vals = {}

        for line in upt_qstn_lines:
            answer_val = ''
            if line.answer_type in ['char_box', 'numerical_box']:
                answer_val = getattr(line, f'value_{line.answer_type}')
            elif line.answer_type == 'text_box' and line.value_text_box:
                answer_val = textwrap.shorten(line.value_text_box, width=50, placeholder=" [...]")
            elif line.answer_type == 'date':
                answer_val = fields.Date.to_string(line.value_date)
            elif line.answer_type == 'datetime':
                answer_val = fields.Datetime.to_string(line.value_datetime)
            elif line.answer_type == 'suggestion':
                answer_val = f'{line.suggested_answer_id.value}: {line.matrix_row_id.value}' if line.matrix_row_id else line.suggested_answer_id.value

            field_type = line.question_id.contact_field_id.ttype
            field_name = line.question_id.contact_field_id.name
            field_relation = line.question_id.contact_field_id.relation
            if field_type not in ['many2one', 'many2many', 'binary', 'selection']:
                vals[field_name] = answer_val
            elif field_type == 'many2one':
                related_model_obj = request.env[field_relation].sudo().search([('name', '=', answer_val)], limit=1)
                vals[field_name] = related_model_obj.id
            elif field_type == 'selection':
                if field_name == 'kg_gender':
                    if answer_val == 'I prefer not to mention':
                        answer_val = 'no_pref'
                vals[field_name] = answer_val.lower()
            if answer.partner_id:
                vals['email'] = answer.email
                vals['mobile'] = answer.mobile_no
                answer.partner_id.sudo().write(vals)
            else:
                vals['email'] = answer.email
                vals['mobile'] = answer.mobile_no
                partner = request.env['res.partner'].sudo().create(vals)
                answer.partner_id = partner.id
        return result

    # def _prepare_survey_finished_values(self, survey, answer, token=False):
    #     values = {'survey': survey, 'answer': answer}
    #     if token:
    #         values['token'] = token
    #
    #     upt_qstn_lines = answer.user_input_line_ids.filtered(lambda x: x.question_id.update_result)
    #     vals = {}
    #
    #     for line in upt_qstn_lines:
    #         answer_val = ''
    #         if line.answer_type in ['char_box', 'numerical_box']:
    #             answer_val = getattr(line, f'value_{line.answer_type}')
    #         elif line.answer_type == 'text_box' and line.value_text_box:
    #             answer_val = textwrap.shorten(line.value_text_box, width=50, placeholder=" [...]")
    #         elif line.answer_type == 'date':
    #             answer_val = fields.Date.to_string(line.value_date)
    #         elif line.answer_type == 'datetime':
    #             answer_val = fields.Datetime.to_string(line.value_datetime)
    #         elif line.answer_type == 'suggestion':
    #             answer_val = f'{line.suggested_answer_id.value}: {line.matrix_row_id.value}' if line.matrix_row_id else line.suggested_answer_id.value
    #
    #         field_type = line.question_id.contact_field_id.ttype
    #         field_name = line.question_id.contact_field_id.name
    #         field_relation = line.question_id.contact_field_id.relation
    #         if field_type not in ['many2one', 'many2many', 'binary', 'selection']:
    #             vals[field_name] = answer_val
    #         elif field_type == 'many2one':
    #             related_model_obj = request.env[field_relation].sudo().search([('name', '=', answer_val)], limit=1)
    #             vals[field_name] = related_model_obj.id
    #         elif field_type == 'selection':
    #             if field_name == 'kg_gender':
    #                 if answer_val == 'I prefer not to mention':
    #                     answer_val = 'no_pref'
    #             vals[field_name] = answer_val.lower()
    #
    #     # if vals.get('email'):
    #     #     email = vals['email'].strip()
    #     #     partner = request.env['res.partner'].sudo().search([('email', '=', email)], limit=1)
    #     # elif vals.get('name'):
    #     #     partner = request.env['res.partner'].sudo().search([('name', '=', vals['name'])], limit=1)
    #     # else:
    #     #     partner = answer.partner_id
    #     #
    #     # if vals:
    #     #     if not partner:
    #     #         partner = request.env['res.partner'].sudo().create(vals)
    #     #         answer.partner_id = partner.id
    #     #     else:
    #     #         answer.partner_id = partner.id
    #     #         partner.sudo().write(vals)
    #
    #     return values
