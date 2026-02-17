# -*- coding: utf-8 -*-
from datetime import date

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    groups_approved_ids = fields.Many2many('res.groups', string="Groups", store=True)
    group_id = fields.Many2one('res.groups', string="Groups", domain="[('id', 'in', groups_approved_ids)]")
    users = fields.Many2many('res.users', 'user_rel', 'user_id', 'employee_id', string="Users",
                             related='group_id.users', store=True)
    operating_unit_id = fields.Many2one('operating.unit', string="Operating Unit", default=lambda self: (
        self.env["res.users"].operating_unit_default_get(self.env.uid)))
    gsn_number = fields.Integer('GSM No.')
    usage_limit = fields.Float('Limit')

    def write(self, vals):
        res = super().write(vals)
        if vals.get('group_id'):
            if self.user_id:
                for approved in self.groups_approved_ids:
                    if self.group_id != approved:
                        approved.users = [(3, self.user_id.id)]
                self.group_id.users = [(4, self.user_id.id)]
        return res

    @api.onchange('id_expiry_date', 'passport_expiry_date', 'birthday', 'visa_expire', 'work_permit_expiration_date')
    def onchange_dates(self):
        if self.work_permit_expiration_date and self.work_permit_expiration_date < date.today():
            raise ValidationError(_('Work Permit Expiration Date should not be past date'))
        if self.visa_expire and self.visa_expire < date.today():
            raise ValidationError(_('Visa expiry date should not be past date'))
        if self.birthday and self.birthday > date.today():
            raise ValidationError(_('Birthdate should not be future date'))


