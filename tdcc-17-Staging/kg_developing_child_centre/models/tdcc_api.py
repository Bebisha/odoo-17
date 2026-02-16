from odoo import models, _
from odoo.exceptions import UserError, ValidationError
import requests
import json

import logging

_logger = logging.getLogger(__name__)


class TDCCApi(models.AbstractModel):
    _name = 'tdcc.api'
    _description = 'TDCC Nabith Integration API Mixin'


    # def post(self, data=None, url=None):
    #     try:
    #         headers = {
    #             # "Host": 'secure-wms.com',
    #             # "Content-Type": 'application/json; charset=utf-8',
    #             "Accept": 'application/hal+json',
    #             # "Authorization": auth_token,
    #             "Accept-Language": 'en-US,en;q=0.8',
    #             "Content-Length": '1072'
    #         }
    #         response = requests.post(url, headers=headers, json=data)
    #     except:
    #         raise ValidationError("Something went wrong!!")
    #     if 'ErrorCode' in response.json():
    #         self.handle_error(response)
    #     return response
    #
    # def handle_error(self, response):
    #     response_data = response.json()
    #     res_property = response_data['Properties'][0]
    #     raise ValidationError(_("ErrorCode:%s in TDCC") % (response_data['ErrorCode']))

    def post(self, data=None, url=None):
        try:
            headers = {
                # "Host": 'secure-wms.com',
                # "Content-Type": 'application/json; charset=utf-8',
                "Accept": 'application/hal+json',
                # "Authorization": auth_token,
                "Accept-Language": 'en-US,en;q=0.8',
                "Content-Length": str(len(json.dumps(data)))
            }
            response = requests.post(url, headers=headers, json=data)
        except Exception as e:
            raise ValidationError(_("Something went wrong!!") + str(e))

        if 'ErrorCode' in response.headers.get('Content-Type', ''):
            self.handle_error(response)

        return response

    def handle_error(self, response):
        response_data = response.json()
        res_property = response_data['Properties'][0]
        raise ValidationError(_("ErrorCode:%s in TDCC") % (response_data['ErrorCode']))
