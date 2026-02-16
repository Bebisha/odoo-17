# -*- coding: utf-8 -*-
from odoo import http
import logging, json
from odoo.http import request

_logger = logging.getLogger(__name__)


class EmiratesIdPost(http.Controller):

    @http.route('/fetch/emiratesid/details/<int:user_id>', type="json", auth="public")
    def fetch_eid_details(self, user_id=None):
        values = json.loads(request.httprequest.data)
        if user_id:
            request.env['kg.emiratesid.scan'].sudo().create(
                {'name': values.get('FullNameEn'), 'data': values, 'user_id': user_id})
