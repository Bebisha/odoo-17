# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import datetime

class AttendanceAttendance(models.Model):
    _name = 'attendance.attendance'
    _description = 'Attendance'
    _rec_name = 'student_id'

    date = fields.Date(string='Date')
    classroom_id = fields.Many2one('school.classroom', string='Classroom')
    student_id = fields.Many2one('res.partner',
                                 domain=[('is_student', '=', True)],
                                 string='Student')
    remark = fields.Text(string='Remark', copy=False)
    status = fields.Selection([('present', 'Present'),
                               ('absent', 'Absent')],
                               default='present',
                               string='Status',
                               copy=False)
    educator_id = fields.Many2one('res.users', string='Educator')
    sheet_id = fields.Many2one('eip.attendance.sheet', string='Sheet')
    
    @api.onchange('classroom_id')
    def onchange_classroom_id(self):
        res = {'domain': {'student_id':
                          [('id', 'in', [])]},
               'value': {'student_id': False}}
        if self.classroom_id.student_ids:
            students_ids = self.classroom_id.student_ids.ids
            domain = {'student_id': [('id', 'in', students_ids)]}
            res.update({'domain': domain})
        return res


class EipAttendanceSheet(models.Model):
    _name = 'eip.attendance.sheet'
    _description = 'EIP Attendance Sheet'
    _rec_name = 'classroom_id'
    
    date = fields.Date(string='Date')
    educator_id = fields.Many2one('res.users', string='Educator')
    classroom_id = fields.Many2one('school.classroom', string='Classroom')
    att_lines = fields.One2many('attendance.attendance','sheet_id',
                                string='Attendance Lines')
