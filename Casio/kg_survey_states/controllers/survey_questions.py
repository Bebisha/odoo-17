# -*- coding: utf-8 -*-
import json
from odoo import http
from odoo.http import request


class SurveyQuestion(http.Controller):

    @http.route('/fetch/survey/answers', methods=["POST"], type="json", auth="none", csrf=False)
    def fetch_answers_ques(self, **post):
        print(post, 'postpost')
        model = post.get('model')
        result = []
        answerid = post.get('answer_id')
        answer_id = request.env[model].sudo().browse(int(answerid))
        question_id = answer_id.question_id
        child_ques_id = request.env[question_id._name].sudo().search([('parent_id', '=', question_id.id)], limit=1)
        record_sets = request.env[child_ques_id.model_id.model].sudo().search(
            [(child_ques_id.model_field_id.name, 'ilike', answer_id.value)])
        print(record_sets,'setsssssssssss')
        for rec in record_sets:
            result.append(rec.name)
        return result
