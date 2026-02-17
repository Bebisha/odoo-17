# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AcademicYear(models.Model):
    _name = 'academic.year'
    _description = 'Academic Year'

    name = fields.Char(string="Name")
    code = fields.Char(string="Code")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    term_ids = fields.One2many("academic.term",
                               inverse_name="academic_year_id",
                               string="Terms")
    current = fields.Boolean(string="Current")
    description = fields.Text(string="Description")
    clinic_id = fields.Many2one('res.company', string="Clinic",
                                default=lambda self:
                                self.env.user.company_id.id)
    active = fields.Boolean(string="Active", default=True)

    @api.constrains('current')
    def _check_current(self):
        """
            - Check one year is active at a time
        """
        old_academy_year_recs = self.search([('id', 'not in', self.ids)])
        total_old_current = old_academy_year_recs.mapped('current').count(True)
        for year in self:
            if year.current:
                total_old_current += 1
        if total_old_current > 1:
            raise ValidationError("You can not select multiple current year")

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        """
            - Starting date must be prior to the ending date
            - Check dates are not overlapped with existing academic year
        """
        for ay in self:

            # Starting date must be prior to the ending date
            start_date = ay.start_date
            end_date = ay.end_date
            current_id = ay.id
            if end_date < start_date:
                raise ValidationError(_('The ending date must not be prior\
                                                    to the starting date.'))

            #  check dates are not overlapped with existing academic year
            domain = [
                ('id', '!=', current_id),
                ('start_date', '<=', end_date),
                ('end_date', '>=', start_date),
            ]
            if self.search_count(domain) > 0:
                raise ValidationError(_('You can not have an overlap with\
                                existing academic year, please correct the\
                                start and or end dates of your current year.'))


class AcademicTerm(models.Model):
    _name = 'academic.term'
    _description = 'Academic Term'

    name = fields.Char(string="Name")
    code = fields.Char(string="Code")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    academic_year_id = fields.Many2one("academic.year",
                                       string="Academic Year")
    description = fields.Text(string="Description")
    clinic_id = fields.Many2one('res.company', string="Clinic",
                                default=lambda self:
                                self.env.user.company_id.id)
    active = fields.Boolean(string="Active", default=True)

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        """
            - Starting date must be prior to the ending date
            - Check dates are not overlapped with existing academic year
        """
        for am in self:

            # Starting date must be prior to the ending date
            start_date = am.start_date
            end_date = am.end_date
            current_id = am.id
            academic_year_id = am.academic_year_id.id
            if end_date < start_date:
                raise ValidationError(_('The ending date must not be prior\
                                                    to the starting date.'))

            #  check dates are not overlapped with existing academic year
            domain = [
                ('id', '!=', current_id),
                ('start_date', '<=', end_date),
                ('end_date', '>=', start_date),
                ('academic_year_id', '=', academic_year_id)
            ]
            if self.search_count(domain) > 0:
                raise ValidationError(_('You can not have an overlap with\
                                existing academic year, please correct the\
                                start and or end dates of your current year.'))
