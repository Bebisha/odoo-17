import datetime
import functools
import json
import logging
from datetime import date
from odoo import api, models
from odoo import http, _
from odoo.addons.kg_base_api.common import (valid_response, invalid_response, ROUTE_BASE, get_user)
from odoo.addons.web.controllers.main import Session
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.exceptions import UserError
from odoo.http import request

_logger = logging.getLogger(__name__)


def json_exception_handler(func):
    """Calls the given function by by-passing the error and convert it to a
        json/http response type(dedicated to only json type requests.)"""

    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except (AccessError, MissingError) as e:
            return invalid_response('Access/Missing Error', e, 503, False)
        except (UserWarning, UserError) as e:
            return invalid_response('User Error/Warning', e, 503, False)
        # except Exception as e:
        #     if 'is not present in table' in str(e):
        #         return invalid_response('Invalid Argument',
        #                                 'One of the passed values(database ID) does not exist or has been deleted in the server.', 503,
        #                                 False)
        #     return invalid_response('Unknown Exception', e, 503, False)

    return wrap


# def validate_json_token(func):
#     @functools.wraps(func)
#     def wrap(self, *args, **kwargs):
#         """."""
#         access_token = request.httprequest.headers.get("session_token")
#         # data = json.loads(request.httprequest.data)
#         # access_token = data.get("session_token")
#         if not access_token:
#             return invalid_response("Token Not Found",
#                                     "missing access token(session_token) in request header", 401, is_http=False)
#         access_token_payload = (
#             request.env["api.access_token"].sudo().search([("token", "=", access_token)], order="id DESC", limit=1)
#         )
#
#         if access_token_payload.find_one_or_create_token(user_id=access_token_payload.user_id.id) != access_token:
#             return invalid_response("Token Expired", "token seems to have expired or invalid", 401, is_http=True)
#
#         request.session.uid = access_token_payload.user_id.id
#         request.uid = access_token_payload.user_id.id
#         return func(self, *args, **kwargs)
#
#     return wrap


class CustomerLeadApi(http.Controller):

    # @validate_json_token
    @json_exception_handler
    @http.route('/create_customer_crm', type="json", auth="public", methods=["POST"])
    def create_customer_crm(self, **post):
        if post.get('uid') and post.get('session_id'):
            user_id = request.env['res.users'].sudo().search(
                [('id', '=', post.get('uid')), ('session_id', '=', post.get('session_id'))])
            if not user_id:
                return valid_response(False, message='Lead creation failed. Authentication issue.')
        config_setting = request.env['ir.config_parameter'].sudo().get_param('customer_data_api.crm_team_id')
        crm_team_rec = request.env['crm.team'].sudo().browse(int(config_setting))
        crm_team_user = crm_team_rec.user_id.id
        lead_name, customer_email, customer_mobile, contact_person_name, contact_person_company_name = False, False, False, False, False

        # post = json.loads(request.httprequest.post)
        if post.get('name'):
            lead_name = post.get('name')
        else:
            lead_name = "Enquiry for Account App"
        if post.get('email_from'):
            customer_email = post.get('email_from')
        if post.get('mobile'):
            customer_mobile = post.get('mobile')
        if post.get('contact_name'):
            contact_person_name = post.get('contact_name')
        if post.get('partner_name'):
            contact_person_company_name = post.get('partner_name')
        vals = {
            'type': 'lead',
            'name': lead_name if lead_name else '',
            'email_from': customer_email if customer_email else '',
            'mobile': customer_mobile if customer_mobile else '',
            'contact_name': contact_person_name if contact_person_name else '',
            'partner_name': contact_person_company_name if contact_person_company_name else '',
            'user_id': crm_team_user,
            'team_id': crm_team_rec.id,
        }
        lead_record = request.env['crm.lead'].sudo().create(vals)
        if lead_record.email_from:
            self.send_cust_accounting_app_request_email_crm_team_lead(lead_record)
            self.send_acknowledgment_email(lead_record)
            return valid_response(lead_record.id, message='Lead created successfully')
        else:
            return valid_response(False, message='Lead creation failed')

    def send_acknowledgment_email(self, lead_record):
        if lead_record:
            to_email = lead_record.email_from
            from_email = request.env.user.company_id.email
            subject = _('Acknowledgement')
            body_html = f"Hi" + ' ' + str(
                lead_record.contact_name) + ',' + " <br/> Your Request for Accounting App has been sent to the Sales Person." \
                        + "<br/><br/>Thanks and Regards.<br/>" + str(request.env.company.name)

            mail_values = {
                'email_from': from_email,
                'email_to': to_email,
                'subject': subject,
                'body_html': body_html,
            }
            mail_id = request.env['mail.mail'].sudo().create(mail_values)
            mail_id.sudo().send()

    def send_cust_accounting_app_request_email_crm_team_lead(self, lead_record):
        crm_team_id = request.env['res.config.settings'].sudo().get_values()['crm_team_id']
        if not crm_team_id:
            raise UserError(_("Please configure CRM Team in CRM Setting"))
        crm_team_rec = request.env['crm.team'].sudo().browse(crm_team_id)
        crm_lead_name = crm_team_rec.sudo().user_id.name

        if crm_team_rec.sudo().user_id:
            to_email = crm_team_rec.user_id.sudo().partner_id.email
            from_email = request.env.user.sudo().company_id.email
            subject = _('Request for Accounting App')
            body_html = f"Hello" + ' ' + str(crm_lead_name) + ',' + " <br/> An Enquiry for Accounting App received from" \
                        + ' ' + str(lead_record.contact_name) + '.' + "<br/><br/>Thanks and Regards.<br/>" + str(
                request.env.company.name)
            mail_values = {
                'email_from': from_email,
                'email_to': to_email,
                'subject': subject,
                'body_html': body_html,
            }
            mail_id = request.env['mail.mail'].sudo().create(mail_values)
            mail_id.sudo().send()
        else:
            raise UserError(_("Please assign a Team Leader"))


class Http(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        res = super(Http, self).session_info()
        if res.get('uid'):
            user_id = self.env['res.users'].sudo().browse(int(res.get('uid')))
            user_id.update({'session_id': False})
        if user_id:
            user_id.update({'session_id': request.session.sid})
            res['session_id'] = request.session.sid
        return res


class SessionInherit(Session):

    @http.route('/web/session/authenticate', type='json', auth="none")
    def authenticate(self, db, login, password, base_location=None):
        user_id = request.env['res.users'].sudo().search([('login', '=', login)])
        for rec in user_id:
            rec.update({'session_id': False})
        res = super(SessionInherit, self).authenticate(db, login, password, base_location=None)
        return res
