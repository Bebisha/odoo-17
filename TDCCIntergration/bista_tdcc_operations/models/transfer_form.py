# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class TranserForm(models.Model):
    _name = 'transfer.form'
    _description = 'Transfer Form'
    _rec_name = 'school_center'

    school_center = fields.Char(string="For the attention of")
    student_id = fields.Many2one("res.partner",
                                 string="Child’s Full Name")
    dob = fields.Date(string="Date of Birth", related="student_id.dob")
    nationality_id = fields.Many2one("res.country",
                                     string="Nationality")
    attendance_start_date = fields.Date(string="Date started\
                                            attendance at TDCC")
    attendance_end_date = fields.Date(string="Date finished\
                                                attendance at TDCC")
    attainment_level = fields.Char(string="Level of attainment\
                                            when finished attendance at TDCC")

    @api.constrains('attendance_start_date', 'attendance_end_date')
    def _check_dates(self):
        """
            - Starting date must be prior to the ending date
        """
        for tf in self:

            # Starting date must be prior to the ending date
            start_date = tf.attendance_start_date
            end_date = tf.attendance_end_date
            if end_date < start_date:
                raise ValidationError(_('The ending date must not be prior\
                                                    to the starting date.'))
