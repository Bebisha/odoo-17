import ast
import functools
import json
import logging

from odoo import http
from odoo.addons.kg_base_api.common import (extract_arguments, invalid_response, invalid_http_response,
                                            valid_response, valid_http_response)
from odoo.exceptions import AccessError
from odoo.http import request

_logger = logging.getLogger(__name__)


def validate_http_token(func):

    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        """."""
        access_token = request.httprequest.headers.get("session_token")
        if not access_token:
            return invalid_http_response("access_token_not_found", "missing access token(session_token) in request header", 401)
        access_token_data = (
            request.env["api.access_token"].sudo().search([("token", "=", access_token)], order="id DESC", limit=1)
        )

        if access_token_data.find_one_or_create_token(user_id=access_token_data.user_id.id) != access_token:
            return invalid_http_response("access_token", "token seems to have expired or invalid", 401)

        request.session.uid = access_token_data.user_id.id
        request.uid = access_token_data.user_id.id
        return func(self, *args, **kwargs)

    return wrap


def validate_token(func):
    """."""

    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        """."""
        access_token = request.httprequest.headers.get("session_token")
        if not access_token:
            return invalid_response("access_token_not_found", "missing access token(session_token) in request header", 401)
        access_token_data = (
            request.env["api.access_token"].sudo().search([("token", "=", access_token)], order="id DESC", limit=1)
        )

        if access_token_data.find_one_or_create_token(user_id=access_token_data.user_id.id) != access_token:
            return invalid_response("access_token", "token seems to have expired or invalid", 401)

        request.session.uid = access_token_data.user_id.id
        request.uid = access_token_data.user_id.id
        return func(self, *args, **kwargs)

    return wrap


_routes = ["/api/<model>", "/api/<model>/<id>", "/api/<model>/<id>/<action>"]


class APIController(http.Controller):
    """."""

    def __init__(self):
        self._model = "ir.model"

    def _call_dynamic_function(self, model, action, data, request_type='json'):
        args = data
        try:
            record = request.env[model].sudo()
            _callable = hasattr(record, action)
            if _callable:
                # action is a dynamic variable.
                values = getattr(record, action)(args) if args else getattr(record, action)()
            else:
                if request_type == 'http':
                    return invalid_http_response(
                        "invalid object or method",
                        "The given action '%s' cannot be performed on record because '%s' has no such method"
                        % (action, model),
                        404,
                    )
                return invalid_response(
                    "invalid object or method",
                    "The given action '%s' cannot be performed on record because '%s' has no such method"
                    % (action, model),
                    404,
                )
        except Exception as e:
            return invalid_response("exception", e, 503) if request_type == 'json' else invalid_http_response(
                "exception", e, 503)
        else:
            return valid_response(values, method_type='PATCH') if request_type == 'json' else valid_http_response(
                values, method_type='PATCH')

    @validate_http_token
    @http.route(_routes, type="http", auth="none", methods=["GET"], csrf=False)
    def get(self, model=None, id=None, action=None, **payload):
        """reads records from Odoo database."""
        model = model.replace('_', '.')
        data = payload
        if action and id == 'patch':
            return self._call_dynamic_function(model, action, data, request_type='request_type')
        else:
            try:
                ioc_name = model
                model = request.env[self._model].sudo().search([("model", "=", model)], limit=1)
                if model:
                    expected_args = ['limit', 'offset', 'order', 'domain', 'fields']
                    unknown_arg = filter(lambda l: l not in expected_args, data.keys())
                    if unknown_arg:
                        msg = "Following values are not valid keys: %s" % ', '.join(unknown_arg)
                        return invalid_http_response("Wrong Value", msg)
                    domain, fields, offset, limit, order = extract_arguments(**data)
                    data = request.env[model.model].search_read(
                        domain=domain, fields=fields, offset=offset, limit=limit, order=order,
                    )

                    if id:
                        domain = [("id", "=", int(id))]
                        data = request.env[model.model].sudo().search_read(
                            domain=domain, fields=fields, offset=offset, limit=limit, order=order,
                        )
                    if data:
                        return valid_http_response(data)
                    else:
                        return valid_http_response(data)
                return invalid_http_response(
                    "invalid object model", "The model %s is not available in the registry." % ioc_name,
                )
            except AccessError as e:
                return invalid_http_response("Access error", "Error: %s" % e)

    @validate_token
    @http.route(_routes, type="json", auth="none", methods=["POST"], csrf=False)
    def post(self, model=None, id=None, action=None, **payload):
        """Creates records to Odoo database."""
        model = model.replace('_', '.')
        data = json.loads(request.httprequest.data)
        if action and id == 'patch':
            return self._call_dynamic_function(model, action, data)
        else:
            payload = json.loads(request.httprequest.data)
            payload = json.loads(payload)
            model = request.env[self._model].sudo().search([("model", "=", model)], limit=1)
            values = {}
            if model:
                try:
                    # changing IDs from string to int.
                    for k, v in payload.items():

                        if "__api__" in k:
                            values[k[7:]] = ast.literal_eval(v)
                        else:
                            values[k] = v

                    resource = request.env[model.model].create(values)
                except Exception as e:
                    request.env.cr.rollback()
                    return invalid_response("params", e)
                else:
                    data = resource.read()
                    if resource:
                        return valid_response(data, method_type='POST')
                    else:
                        return valid_response(data, method_type='POST')
            return invalid_response("invalid object model", "The model %s is not available in the registry." % model, )

    @validate_token
    @http.route(_routes, type="http", auth="none", methods=["PUT"], csrf=False)
    def put(self, model=None, id=None, **payload):
        """write/update records in Odoo database."""
        model = model.replace('_', '.')
        values = {}
        payload = request.httprequest.data.decode()
        payload = json.loads(payload)
        try:
            _id = int(id)
        except Exception as e:
            return invalid_response("invalid object id", "invalid literal %s for id with base " % id)
        _model = request.env[self._model].sudo().search([("model", "=", model)], limit=1)
        if not _model:
            return invalid_response(
                "invalid object model", "The model %s is not available in the registry." % model, 404,
            )
        try:
            record = request.env[_model.model].sudo().browse(_id)
            for k, v in payload.items():
                if "__api__" in k:
                    values[k[7:]] = ast.literal_eval(v)
                else:
                    values[k] = v
            record.write(values)
        except Exception as e:
            request.env.cr.rollback()
            return invalid_response("exception", e)
        else:
            return valid_response(record.read(), method_type='PUT')

    @validate_token
    @http.route(_routes, type="http", auth="none", methods=["DELETE"], csrf=False)
    def delete(self, model=None, id=None, **payload):
        """unlink/remove records from Odoo database."""
        model = model.replace('_', '.')
        try:
            _id = int(id)
        except Exception as e:
            return invalid_response("invalid object id", "invalid literal %s for id with base " % id)
        try:
            record = request.env[model].sudo().search([("id", "=", _id)])
            if record:
                record.unlink()
            else:
                return invalid_response("missing_record", "record object with id %s could not be found" % _id, 404, )
        except Exception as e:
            request.env.cr.rollback()
            return invalid_response("exception", e.name, 503)
        else:
            return valid_response("record %s has been successfully deleted" % record.id, method_type='DELETE')

    @validate_token
    @http.route(_routes, type="http", auth="none", methods=["PATCH"], csrf=False)
    def patch(self, model=None, id=None, action=None, **payload):
        """helps the controller to call any function from the given model."""
        model = model.replace('_', '.')
        args = payload
        if id == 'patch':
            _id = False
        else:
            try:
                _id = int(id)
            except Exception as e:
                return invalid_response("invalid object id", "invalid literal %s for id with base" % id)
        try:
            if _id:
                record = request.env[model].sudo().search([("id", "=", _id)], limit=1)
                _callable = action in [method for method in dir(record) if callable(getattr(record, method))]
            else:
                record = request.env[model].sudo()
                _callable = hasattr(record, action)
            if not record and _id:
                return invalid_response(
                    "invalid object",
                    "The given id %s is not valid for the record %s."
                    % (_id, record),
                    404,
                )
            if _callable:
                # action is a dynamic variable.
                values = getattr(record, action)(args) if args else getattr(record, action)()
            else:
                return invalid_response(
                    "invalid object or method",
                    "The given action '%s' cannot be performed on record because '%s' has no such method"
                    % (action, model),
                    404,
                )
        except Exception as e:
            return invalid_response("exception", e, 503)
        else:
            return valid_response(values, method_type='PATCH')
