import json
import logging

from odoo import http, _
from odoo.addons.kg_base_api.common import invalid_response, _convert_image_to_base64
from odoo.exceptions import AccessDenied, AccessError, UserError
from odoo.http import request
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class AccessToken(http.Controller):

    @http.route("/session/test", methods=["GET"], type="http", auth="none", csrf=False)
    def login_test(self, **post):
        """Generates a new token f"""

    @http.route("/session/login", methods=["POST"], type="json", auth="none", csrf=False)
    def token(self, **post):
        """Generates a new token for the passed user if no valid session found."""
        _token = request.env["api.access_token"]
        data = json.loads(request.httprequest.data)
        db, username, password, device_id = (
            data.get("db"),
            data.get("email"),
            data.get("password"),
            data.get("device_id"),
        )
        _credentials_includes_in_body = all([db, username, password, device_id])
        if not _credentials_includes_in_body:
            # The request post body is empty the credetials maybe passed via the headers.
            headers = request.httprequest.headers
            db = headers.get("db")
            username = headers.get("login")
            password = headers.get("password")
            device_id = headers.get("device_id")
            _credentials_includes_in_headers = all([db, username, password, device_id])
            if not _credentials_includes_in_headers:
                # Empty 'db' or 'username' or 'password:
                return invalid_response(
                    "Missing Error", "Either of the following are missing [db, email, password, device_id, vehicle_id]",
                    403,
                )
        # Login in odoo database:
        try:
            request.session.authenticate(db, username, password)
        except AccessError as aee:
            return invalid_response("Access error", "Error: %s" % aee.name)
        except AccessDenied as ade:
            return invalid_response("Access denied", "Login, password or db invalid")
        except Exception as e:
            # Invalid database:
            info = "The database name is not valid {}".format((e))
            error = "invalid_database"
            _logger.error(info)
            return invalid_response("wrong database name", error, 403)

        uid = request.session.uid
        # odoo login failed:
        if not uid:
            info = "authentication failed"
            error = "authentication failed"
            _logger.error(info)
            return invalid_response(401, error, info)

        # Generate tokens
        access_token = _token.find_one_or_create_token(user_id=uid, create=True)
        # Successful response:
        user = request.env.user
        # user = request.env['res.users'].browse(uid)
        team = request.env['hr.employee.public'].sudo().search([('user_id', '=', user.id)])
        date_today = date.today()
        overdue_tasks = request.env['project.task'].sudo().search_count(
            [('user_ids', 'in', user.id), ('stage_id.is_closed', '=', False), ('date_deadline', '<', date_today)])
        progress_tasks = request.env['project.task'].sudo().search_count(
            [('user_ids', 'in', user.id), ('stage_id.is_open', '=', False), ('stage_id.is_closed', '=', False)])
        url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        device_login_line = user.login_ids.filtered(lambda x: x.device_id == device_id and not x.signout)
        if device_login_line:
            device_login_line.write({'signin': datetime.now(), 'is_active': True})
        else:
            val = {'login_id': user.id, 'device_id': device_id, 'signin': datetime.now(), 'is_active': True}
            request.env['login.details.line'].create(val)

        return {
            "uid": uid,
            "message": "Login successful",
            "status": True,
            "status_code": 200,
            # "user_context": request.session.get_context() if uid else {},
            "user_name": request.env.user.name or '',
            "user_id": request.env.user.id or 0,
            "partner_id": request.env.user.partner_id.id or 0,
            "access_token": access_token or '',
            "company_id": request.env.user.company_id.id or 0,
            "company_name": request.env.user.company_id.name or '',
            "currency": request.env.user.currency_id.name or '',
            "currency_decimal_places": 3 or request.env.user.currency_id.decimal_places or 0,
            "country": request.env.user.country_id.name if uid else '',
            "country_id": request.env.company.country_id.id if uid else '',
            "contact_address": request.env.user.contact_address or '',
            "customer_rank": request.env.user.customer_rank or 0,
            "user_image": _convert_image_to_base64(
                request.env.user.image_128 or request.env.user.partner_id.image_128) or '',
            "team_name": team.department_id.name or '',
            "team_id": team.department_id.id or 0,
            "email_id": team.work_email or '',
            "phone_no": team.work_phone or '',
            "profile_image": team.avatar_1920 or '',
            "designation": team.department_id.name or '',
            "team_lead": team.coach_id.name or '',
            "team_lead_id": team.coach_id.id or 0,
            "overdue_tasks": overdue_tasks or 0,
            "inprogress_tasks": progress_tasks or 0,
            'device_id': device_id

        }

    @http.route("/session/authenticate", methods=["POST"], type="json", auth="none", csrf=False)
    def session_token(self, **post):
        """Generates a new token for the passed user if no valid session found."""
        _token = request.env["api.access_token"]
        data = json.loads(request.httprequest.data)
        _logger.info('Dataaaaaaaaaaaaaaaa %s',data)
        db, username, password = (
            data.get("db"),
            data.get("email"),
            data.get("password"),
        )
        _credentials_includes_in_body = all([db, username, password])
        if not _credentials_includes_in_body:
            # The request post body is empty the credetials maybe passed via the headers.
            headers = request.httprequest.headers
            db = headers.get("db")
            username = headers.get("login")
            password = headers.get("password")
            _credentials_includes_in_headers = all([db, username, password])
            if not _credentials_includes_in_headers:
                # Empty 'db' or 'username' or 'password:
                return invalid_response(
                    "Missing Error", "Either of the following are missing [db, email, password, device_id, vehicle_id]",
                    403,
                )
        # Login in odoo database:
        try:
            request.session.authenticate(db, username, password)
        except AccessError as aee:
            return invalid_response("Access error", "Error: %s" % aee.name)
        except AccessDenied as ade:
            return invalid_response("Access denied", "Login, password or db invalid")
        except Exception as e:
            # Invalid database:
            info = "The database name is not valid {}".format((e))
            error = "invalid_database"
            _logger.error(info)
            return invalid_response("wrong database name", error, 403)
        print('ssssss')
        uid = request.session.uid
        # # odoo login failed:
        if not uid:
            info = "authentication failed"
            error = "authentication failed"
            _logger.error(info)
            return invalid_response(401, error, info)
        #
        # Generate tokens
        access_token = _token.find_one_or_create_token(user_id=uid, create=True)
        _logger.info('Access_tokennnnnnn %s',access_token)

        # Successful response:
        user = request.env.user
        team = request.env['hr.employee.public'].sudo().search([('user_id', '=', user.id)])

        return {
                "uid": uid,
                "message": "Login successful",
                "status": True,
                "status_code": 200,
                "user_name": request.env.user.name or '',
                "user_id": request.env.user.id or 0,
                "partner_id": request.env.user.partner_id.id or 0,
                "access_token": access_token or '',
                "company_id": request.env.user.company_id.id or 0,
                "company_name": request.env.user.company_id.name or '',
                "currency": request.env.user.currency_id.name or '',
                "currency_decimal_places": 3 or request.env.user.currency_id.decimal_places or 0,
                "country": request.env.user.country_id.name if uid else '',
                "country_id": request.env.company.country_id.id if uid else '',
                "contact_address": request.env.user.contact_address or '',
                "customer_rank": request.env.user.customer_rank or 0,
                "user_image": _convert_image_to_base64(
                    request.env.user.image_128 or request.env.user.partner_id.image_128) or '',
                "email_id": team.work_email or '',
                "phone_no": team.work_phone or '',
                "profile_image": team.avatar_1920 or '',
                "designation": team.department_id.name or '',
                "team_lead": team.coach_id.name or '',
                "team_lead_id": team.coach_id.id or 0,

        }

        #
        # return {
        #     "uid": uid,
        #     "message": "Login successful",
        #     "status": True,
        #     "status_code": 200,
        #     "user_context": request.session.get_context() if uid else {},
        #     "user_name": request.env.user.name or '',
        #     "user_id": request.env.user.id or 0,
        #     "partner_id": request.env.user.partner_id.id or 0,
        #     "access_token": access_token or '',
        #     "company_id": request.env.user.company_id.id or 0,
        #     "company_name": request.env.user.company_id.name or '',
        #     "currency": request.env.user.currency_id.name or '',
        #     "currency_decimal_places": 3 or request.env.user.currency_id.decimal_places or 0,
        #     "country": request.env.user.country_id.name if uid else '',
        #     "country_id": request.env.company.country_id.id if uid else '',
        #     "contact_address": request.env.user.contact_address or '',
        #     "customer_rank": request.env.user.customer_rank or 0,
        #     "user_image": _convert_image_to_base64(
        #         request.env.user.image_128 or request.env.user.partner_id.image_128) or '',
        #     "team_name": team.department_id.name or '',
        #     "team_id": team.department_id.id or 0,
        #     "email_id": team.work_email or '',
        #     "phone_no": team.work_phone or '',
        #     "profile_image": team.avatar_1920 or '',
        #     "designation": team.department_id.name or '',
        #     "team_lead": team.coach_id.name or '',
        #     "team_lead_id": team.coach_id.id or 0,
        #     "overdue_tasks": overdue_tasks or 0,
        #     "inprogress_tasks": progress_tasks or 0,
        #     'device_id': device_id
        #
        # }

    @http.route("/session/logout", methods=["POST"], type="json", auth="none", csrf=False)
    def delete(self, **post):
        """Deletes a given token"""

        token = request.env["api.access_token"]
        data = json.loads(request.httprequest.data)
        token_str = data.get("session_token")
        device_id = data.get("device_id")
        access_token = token.search([("token", "=", token_str)], limit=1)
        if not access_token:
            error = "Access token(access-token) is missing in the request body or invalid token was provided"
            return invalid_response(400, error)
        user_id = access_token.user_id
        device_login_line = user_id.login_ids.filtered(lambda x: x.device_id == device_id and x.signin and not x.signout)
        if device_login_line:
            device_login_line.write({'signout': datetime.now(), 'is_active': False})
        else:
            val = {'login_id': user_id.id, 'device_id': device_id, 'signin': datetime.now(),'signout': datetime.now(),'is_active': False}
            request.env['login.details.line'].create(val)

        for token in access_token:
            token.unlink()
        # Successful response:
        return {
            "message": "Logout successful",
            "status": True,
            "status_code": 200,
            "user_id": user_id.id,
        }
