# -*- encoding: utf-8 -*-
#
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
#

from odoo import models, fields, api, _
import warnings

from odoo.exceptions import UserError


class EiipGroup(models.Model):
    _name = 'eiip.group'
    _description = 'EIIP Groups'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code')
    clinic_id = fields.Many2one('res.company', string='Clinic',
                                default=lambda self: self.env.user.company_id)
    faculty_ids = fields.Many2many('res.partner', string='Faculties')
    student_enrollment = fields.One2many('student.enroll', 'group_id',
                                         string='Enroll Students')


class StudentEnroll(models.Model):
    _name = 'student.enroll'
    _description = 'Student Enrollment'

    name = fields.Char(string='Name', required=True)
    student_id = fields.Many2one('res.partner', string='Student',
                                 required=True)
    join_date = fields.Date(string='Join Date')
    end_date = fields.Date(string='End Date')
    group_id = fields.Many2one('eiip.group', string='Group')
    clinic_id = fields.Many2one('res.company', string='Clinic',
                                default=lambda self: self.env.user.company_id)

    @api.onchange('join_date', 'end_date')
    def onchange_join_end_date(self):
        if self.end_date and self.join_date > self.end_date:
            raise UserError(
                _("Join date can not be greater than end date !"))
