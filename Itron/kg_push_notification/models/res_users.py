# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    login_ids = fields.One2many('login.details.line', 'login_id')


class LoginDetails(models.Model):
    _name = 'login.details.line'
    _description = 'Login Details'

    login_id = fields.Many2one('res.users')
    device_id = fields.Char('Device Id')
    signin = fields.Datetime('Sign-in Time')
    signout = fields.Datetime('Sign-out Time')
    is_active = fields.Boolean("Active")

    @api.onchange('signout', 'signin')
    def onchange_signout(self):
        if self.signout:
            self.is_active = False
        elif self.signin:
            self.is_active = True
        else:
            self.is_active = False
