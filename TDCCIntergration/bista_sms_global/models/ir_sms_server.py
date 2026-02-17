# -*- encoding: utf-8 -*-
#
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################

from odoo import fields, models

URL = 'https://www.smsglobal.com/http-api.php?action=sendsms'


class IrSMSServer(models.Model):
    _name = 'ir.sms_server'
    _description = 'SMS Server'
    _order = 'sequence'

    sequence = fields.Integer(string='Priority', copy=False, default=10)
    name = fields.Char(string='Name', copy=False, required=True)
#     login_url = fields.Char(string='Login URL')
#     submit_button = fields.Char(string='Submit Button as')
    username = fields.Char(string='Username', copy=False, required=True)
    password = fields.Char(string='Password', copy=False, required=True)
    send_sms_url = fields.Char(string='Send SMS URL', required=True, default=URL)
    from_no = fields.Char(string="From", required=True)
