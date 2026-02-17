# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
import logging
import werkzeug
from datetime import datetime
from math import ceil

from dateutil.relativedelta import relativedelta

from odoo import fields, http, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.http import request
from odoo.tools import ustr
from odoo.addons.survey.controllers.main import Survey

_logger = logging.getLogger(__name__)


class SurveyInherit(Survey):
    # HELPER METHODS #
    def _check_bad_cases(self, survey, token=None):
        # In case of bad survey, redirect to surveys list
        if not survey.sudo().exists():
            return werkzeug.utils.redirect("/survey/")

        # In case of auth required, block public user
        if survey.auth_required and request.env.user._is_public():
            return request.render("survey.survey_auth_required", {'survey': survey, 'token': token})

        # In case of non open surveys
        if survey.stage_id.closed:
            return request.render("survey.notopen")

        # If there is no pages
        if not survey.page_ids:
            return request.render("survey.nopages", {'survey': survey})
        # Everything seems to be ok
        return None
    def _check_deadline(self, user_input):
        '''Prevent opening of the survey if the deadline has turned out

        ! This will NOT disallow access to users who have already partially filled the survey !'''
        deadline = user_input.deadline
        if deadline:
            dt_deadline = fields.Datetime.from_string(deadline)
            dt_now = datetime.now()
            if dt_now > dt_deadline:  # survey is not open anymore
                return request.render("survey.notopen")
        return None

    def _get_access_data(self, survey_token, answer_token, ensure_token=True,check_partner=True):
        """ Get back data related to survey and user input, given the ID and access
        token provided by the route.

         : param ensure_token: whether user input existence should be enforced or not(see ``_check_validity``)
        """
        survey_sudo, answer_sudo = request.env['survey.survey'].sudo(), request.env['survey.user_input'].sudo()
        has_survey_access, can_answer = False, False

        validity_code = self._check_validity(survey_token, answer_token, ensure_token=ensure_token,check_partner=check_partner)
        if validity_code != 'survey_wrong':
            survey_sudo, answer_sudo = self._fetch_from_access_token(survey_token, answer_token)
            try:
                survey_user = survey_sudo.with_user(request.env.user)
                survey_user.check_access_rights(self, 'read', raise_exception=True)
                survey_user.check_access_rule(self, 'read')
            except:
                pass
            else:
                has_survey_access = True
            can_answer = bool(answer_sudo)
            if not can_answer:
                can_answer = survey_sudo.access_mode == 'public'

        return {
            'survey_sudo': survey_sudo,
            'answer_sudo': answer_sudo,
            'has_survey_access': has_survey_access,
            'can_answer': can_answer,
            'validity_code': validity_code,
        }

    def _prepare_survey_finished_values(self, survey, answer, token=False):
        values = {'survey': survey, 'answer': answer}
        if token:
            values['token'] = token
        if survey.scoring_type != 'no_scoring' and survey.certification:
            answer_perf = survey._get_answers_correctness(answer)[answer]
            values['graph_data'] = json.dumps([
                {"text": "Correct", "count": answer_perf['correct']},
                {"text": "Partially", "count": answer_perf['partial']},
                {"text": "Incorrect", "count": answer_perf['incorrect']},
                {"text": "Unanswered", "count": answer_perf['skipped']}
            ])
        return values

    def _redirect_with_error(self, access_data, error_key):
        survey_sudo = access_data['survey_sudo']
        answer_sudo = access_data['answer_sudo']

        if error_key == 'survey_void' and access_data['can_answer']:
            return request.render("survey.survey_void_content", {'survey': survey_sudo, 'answer': answer_sudo})
        elif error_key == 'survey_closed' and access_data['can_answer']:
            return request.render("survey.survey_closed_expired", {'survey': survey_sudo})
        elif error_key == 'survey_auth':
            if not answer_sudo:  # survey is not even started
                redirect_url = '/web/login?redirect=/survey/start/%s' % survey_sudo.access_token
            elif answer_sudo.access_token:  # survey is started but user is not logged in anymore.
                if answer_sudo.partner_id and (answer_sudo.partner_id.user_ids or survey_sudo.users_can_signup):
                    if answer_sudo.partner_id.user_ids:
                        answer_sudo.partner_id.signup_cancel()
                    else:
                        answer_sudo.partner_id.signup_prepare(expiration=fields.Datetime.now() + relativedelta(days=1))
                    redirect_url = answer_sudo.partner_id._get_signup_url_for_action(
                        url='/survey/start/%s?answer_token=%s' % (survey_sudo.access_token, answer_sudo.access_token))[
                        answer_sudo.partner_id.id]
                else:
                    redirect_url = '/web/login?redirect=%s' % ('/survey/start/%s?answer_token=%s' % (
                    survey_sudo.access_token, answer_sudo.access_token))
            return request.render("survey.survey_auth_required", {'survey': survey_sudo, 'redirect_url': redirect_url})
        elif error_key == 'answer_deadline' and answer_sudo.access_token:
            return request.render("survey.survey_closed_expired", {'survey': survey_sudo})
        elif error_key in ['answer_wrong_user', 'token_wrong']:
            return request.render("survey.survey_access_error", {'survey': survey_sudo})

        return request.redirect("/")

    # def _redirect_with_error(self, access_data, error_key):
    #     survey_sudo = access_data['survey_sudo']
    #     answer_sudo = access_data['answer_sudo']
    #
    #     if error_key == 'survey_void' and access_data['can_answer']:
    #         return request.render("survey.survey_void", {'survey': survey_sudo, 'answer': answer_sudo})
    #     elif error_key == 'survey_closed' and access_data['can_answer']:
    #         return request.render("survey.survey_expired", {'survey': survey_sudo})
    #     elif error_key == 'survey_auth' and answer_sudo.access_token:
    #         if answer_sudo.partner_id and (answer_sudo.partner_id.user_ids or survey_sudo.users_can_signup):
    #             if answer_sudo.partner_id.user_ids:
    #                 answer_sudo.partner_id.signup_cancel()
    #             else:
    #                 answer_sudo.partner_id.signup_prepare(expiration=fields.Datetime.now() + relativedelta(days=1))
    #             redirect_url = answer_sudo.partner_id._get_signup_url_for_action(
    #                 url='/survey/start/%s?answer_token=%s' % (survey_sudo.access_token, answer_sudo.access_token))[
    #                 answer_sudo.partner_id.id]
    #         else:
    #             redirect_url = '/web/login?redirect=%s' % (
    #                         '/survey/start/%s?answer_token=%s' % (survey_sudo.access_token, answer_sudo.access_token))
    #         return request.render("survey.survey_auth_required", {'survey': survey_sudo, 'redirect_url': redirect_url})
    #     elif error_key == 'answer_deadline' and answer_sudo.access_token:
    #         return request.render("survey.survey_expired", {'survey': survey_sudo})
    #     elif error_key == 'answer_done' and answer_sudo.access_token:
    #         return request.render("survey.survey_fill_form_done", self._prepare_survey_finished_values(survey_sudo, answer_sudo,
    #                                                                                        token=answer_sudo.access_token))
    #
    #     return werkzeug.utils.redirect("/")

    def _check_validity(self, survey_token, answer_token, ensure_token=True, check_partner=True):
        """ Check survey is open and can be taken. This does not checks for
        security rules, only functional / business rules. It returns a string key
        allowing further manipulation of validity issues

         * survey_wrong: survey does not exist;
         * survey_auth: authentication is required;
         * survey_closed: survey is closed and does not accept input anymore;
         * survey_void: survey is void and should not be taken;
         * token_wrong: given token not recognized;
         * token_required: no token given although it is necessary to access the
           survey;
         * answer_done: token linked to a finished answer;
         * answer_deadline: token linked to an expired answer;

        :param ensure_token: whether user input existence based on given access token
          should be enforced or not, depending on the route requesting a token or
          allowing external world calls;
        """
        survey_sudo, answer_sudo = self._fetch_from_access_token(survey_token, answer_token)

        if not survey_sudo.exists():
            return 'survey_wrong'

        if answer_token and not answer_sudo:
            return 'token_wrong'

        if not answer_sudo and ensure_token:
            return 'token_required'
        if not answer_sudo and survey_sudo.access_mode == 'token':
            return 'token_required'

        if survey_sudo.users_login_required and request.env.user._is_public():
            return 'survey_auth'

        if (not survey_sudo.active) and (not answer_sudo or not answer_sudo.test_entry):
            return 'survey_closed'

        if (not survey_sudo.page_ids and survey_sudo.questions_layout == 'page_per_section') or not survey_sudo.question_ids:
            return 'survey_void'

        if answer_sudo and check_partner:
            if request.env.user._is_public() and answer_sudo.partner_id and not answer_token:
                # answers from public user should not have any partner_id; this indicates probably a cookie issue
                return 'answer_wrong_user'
            if not request.env.user._is_public() and answer_sudo.partner_id != request.env.user.partner_id:
                # partner mismatch, probably a cookie issue
                return 'answer_wrong_user'

        # if answer_sudo and answer_sudo.state == 'done':
        #     return 'answer_done'

        if answer_sudo and answer_sudo.deadline and answer_sudo.deadline < datetime.now():
            return 'answer_deadline'

        return True
    def _fetch_from_access_token(self, survey_token, answer_token):
        """ Check that given token matches an answer from the given survey_id.
        Returns a sudo-ed browse record of survey in order to avoid access rights
        issues now that access is granted through token. """
        survey_sudo = request.env['survey.survey'].with_context(active_test=False).sudo().search([('access_token', '=', survey_token)])
        if not answer_token:
            answer_sudo = request.env['survey.user_input'].sudo()
        else:
            answer_sudo = request.env['survey.user_input'].sudo().search([
                ('survey_id', '=', survey_sudo.id),
                ('access_token', '=', answer_token)
            ], limit=1)
        return survey_sudo, answer_sudo

    # @http.route('/survey/start/<string:survey_token>', type='http', auth='public', website=True)
    # def survey_start(self, survey_token, answer_token=None, email=False, **post):
    #     """ Start a survey by providing
    #      * a token linked to a survey;
    #      * a token linked to an answer or generate a new token if access is allowed;
    #     """
    #     # Get the current answer token from cookie
    #     answer_from_cookie = False
    #     if not answer_token:
    #         answer_token = request.httprequest.cookies.get('survey_%s' % survey_token)
    #         answer_from_cookie = bool(answer_token)
    #
    #     access_data = self._get_access_data(survey_token, answer_token, ensure_token=False)
    #
    #     if answer_from_cookie and access_data['validity_code'] in ('answer_wrong_user', 'token_wrong'):
    #         # If the cookie had been generated for another user or does not correspond to any existing answer object
    #         # (probably because it has been deleted), ignore it and redo the check.
    #         # The cookie will be replaced by a legit value when resolving the URL, so we don't clean it further here.
    #         access_data = self._get_access_data(survey_token, None, ensure_token=False)
    #
    #     if access_data['validity_code'] is not True:
    #         return self._redirect_with_error(access_data, access_data['validity_code'])
    #
    #     survey_sudo, answer_sudo = access_data['survey_sudo'], access_data['answer_sudo']
    #     if not answer_sudo:
    #         try:
    #             answer_sudo = survey_sudo._create_answer(user=request.env.user, email=email)
    #         except UserError:
    #             answer_sudo = False
    #
    #     if not answer_sudo:
    #         try:
    #             survey_sudo.with_user(request.env.user).check_access_rights('read')
    #             survey_sudo.with_user(request.env.user).check_access_rule('read')
    #         except:
    #             return request.redirect("/")
    #         else:
    #             return request.render("survey.survey_403_page", {'survey': survey_sudo})
    #     # if answer_sudo.state == 'new':  # Intro page
    #     #     data = {'survey': survey_sudo, 'answer': answer_sudo, 'page': 0}
    #     #     return request.render('survey.survey_fill_form_start', data)
    #     # else:
    #     return request.redirect('/survey/%s/%s' % (survey_sudo.access_token, answer_sudo.access_token))

    # @http.route('/survey/verify/<string:survey_token>/<string:answer_token>', type='http', auth='public', website=True)
    # def display_page(self, survey_token, answer_token, **post):
    #     access_data = self._get_access_data(survey_token, answer_token, ensure_token=True)
    #     if access_data['validity_code'] is not True:
    #         return self._redirect_with_error(access_data, access_data['validity_code'])
    #     answer_sudo = access_data['answer_sudo']
    #     if answer_sudo.state != 'done' and answer_sudo.survey_time_limit_reached:
    #
    #         answer_sudo._mark_done()
    #     if answer_sudo:
    #         answer_sudo.write({'email':post.get('email'),'mobile_no':post.get('mobile_no')})
    #     return request.render('survey.survey_page_fill',
    #                           self._prepare_survey_data(access_data['survey_sudo'], answer_sudo, **post))

    # @http.route(['/survey/verify/<string:survey_token>/<string:answer_token>'],
    #             type='http', auth='public', website=True, csrf=False)
    # # @http.route('/survey/<string:survey_token>/<string:answer_token>', type='http', auth='public', website=True)
    # def verify_page(self, survey_token, answer_token, **post):
    #     access_data = self._get_access_data(survey_token, answer_token, ensure_token=True)
    #     if access_data['validity_code'] is not True:
    #         return self._redirect_with_error(access_data, access_data['validity_code'])
    #     survey_sudo, answer_sudo = access_data['survey_sudo'], access_data['answer_sudo']
    #
    #     if answer_sudo:
    #         answer_sudo.write({'email':post.get('email'),'mobile_no':post.get('mobile_no')})
    #
    #     answer_sudo = access_data['answer_sudo']
    #     if answer_sudo.state != 'done' and answer_sudo.survey_time_limit_reached:
    #         answer_sudo._mark_done()
    #
    #     return request.render('survey.survey_page_fill',
    #                           self._prepare_survey_data(access_data['survey_sudo'], answer_sudo, **post))

        # def verify_survey(self, survey_token, answer_token, prev=None, **post):
    #     access_data = self._get_access_data(survey_token, answer_token, ensure_token=True)
    #     if access_data['validity_code'] is not True:
    #         return self._redirect_with_error(access_data, access_data['validity_code'])
    #
    #     survey_sudo, answer_sudo = access_data['survey_sudo'], access_data['answer_sudo']
    #     if answer_sudo:
    #         answer_sudo.write({'email':post.get('email'),'mobile_no':post.get('mobile_no')})
    #
    #     if survey_sudo.is_time_limited and not answer_sudo.start_datetime:
    #         # init start date when user starts filling in the survey
    #         answer_sudo.write({
    #             'start_datetime': fields.Datetime.now()
    #         })
    #
    #     page_or_question_key = 'question' if survey_sudo.questions_layout == 'page_per_question' else 'page'
    #     # Select the right page
    #     if answer_sudo.state == 'new':  # First page
    #         result = survey_sudo._get_next_page_or_question(answer_sudo, 0, go_back=False)
    #         if isinstance(result, tuple):
    #             page_or_question_id, last = result
    #         else:
    #             page_or_question_id = result
    #             last = False
    #         data = {
    #             'survey': survey_sudo,
    #             page_or_question_key: page_or_question_id,
    #             'answer': answer_sudo
    #         }
    #         if last:
    #             data.update({'last': True})
    #         return request.render('survey.survey_page_fill', data)
    #     elif answer_sudo.state == 'done':  # Display success message
    #         return request.render('survey.survey_fill_form_done', self._prepare_survey_finished_values(survey_sudo, answer_sudo))
    #     elif answer_sudo.state == 'skip':
    #         flag = (True if prev and prev == 'prev' else False)
    #         result = survey_sudo._get_next_page_or_question(answer_sudo, answer_sudo.last_displayed_page_id.id,
    #                                                         go_back=flag)
    #         if isinstance(result, tuple):
    #             page_or_question_id, last = result
    #         else:
    #             page_or_question_id = result
    #             last = False
    #
    #         # special case if you click "previous" from the last page, then leave the survey, then reopen it from the URL, avoid crash
    #         if not page_or_question_id:
    #             result = survey_sudo._get_next_page_or_question(answer_sudo, answer_sudo.last_displayed_page_id.id,
    #                                                             go_back=True)
    #             if isinstance(result, tuple):
    #                 page_or_question_id, last = result
    #             else:
    #                 page_or_question_id = result
    #                 last = False
                # page_or_question_id, last = survey_sudo.next_page_or_question(answer_sudo,
                #                                                               answer_sudo.last_displayed_page_id.id,
                #                                                               go_back=True)

        #     data = {
        #         'survey': survey_sudo,
        #         page_or_question_key: page_or_question_id,
        #         'answer': answer_sudo
        #     }
        #     if last:
        #         data.update({'last': True})
        #
        #     return request.render('survey.survey_page_fill', data)
        # else:
        #     return request.render("survey.403", {'survey': survey_sudo})

        # UserInput = request.env['survey.user_input']
        # user_input = UserInput.sudo().search([('token', '=', token)], limit=1)
        # if user_input:
        #     applicant = request.env['hr.applicant'].sudo().search(
        #         [('email_from', '=', post.get("name")), ('partner_mobile', '=', post.get('mobile'))])
        #     if applicant:
        #         user_input.sudo().write({'email': post.get("name"),'start_datetime': fields.Datetime.now()})
        #         current_time = fields.Datetime.now()
        #
        #         message = ''
        #         start_button = True
        #         if survey.end_time < current_time:
        #             message = "Exam time finished! Try Next time!"
        #             start_button = False
        #         if survey.start_time < current_time < survey.end_time:
        #             time_delta = (survey.end_time - current_time)
        #             total_seconds = time_delta.total_seconds()
        #             time_limit = total_seconds / 60
        #             user_input.sudo().write({'time_limit': time_limit})
        #             message = 'Exam already started and exam will end at %s'%(survey.end_time)
        #         if survey.start_time > current_time:
        #             message = 'Exam will start at %s only ' %(survey.start_time)
        #             start_button = False
        #         if survey.start_time == current_time:
        #             message = ""
        #         data = {'survey': survey, 'user_name': post.get('name'), 'mobile': post.get('mobile'), 'page': None,'end_secs':3000,
        #                 'token': user_input.token,'start_time':survey.start_time,'end_time':survey.end_time,'message':message,'start_button':start_button}
        #         return request.render('online_exam.exam_start', data)
        #     else:
        #         data = {'survey': survey, 'user_name': post.get('name'), 'mobile': post.get('mobile'), 'page': None,
        #                 'token': user_input.token}
        #         return request.render('online_exam.verification_failed', data)

