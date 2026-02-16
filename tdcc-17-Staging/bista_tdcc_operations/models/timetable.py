# -*- encoding: utf-8 -*-
#
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
#

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from collections import OrderedDict


class TimeTable(models.Model):
    _name = 'time.table'
    _description = 'Time Table'

    name = fields.Char(string="Name")
    lead_educator_id = fields.Many2one("res.partner",
                                       string="Lead Educator")
    educator_id = fields.Many2one("res.partner",
                                  string="Educator")
    speech_therapist_id = fields.Many2one("res.partner",
                                          string="Speech and\
                                          Language Therapist")
    occupational_therapist_id = fields.Many2one("res.partner",
                                                string="Occupational\
                                                Therapist")
    term_id = fields.Many2one("academic.term",
                              string="Term beginning")
    class_id = fields.Many2one("school.classroom", string="Class")
    date_from = fields.Date(string="Start Date")
    date_to = fields.Date(string="End Date")
    timetable_line_ids = fields.One2many("time.table.line",
                                         inverse_name="timetable_id",
                                         string="Time Table Lines")
    student_ids = fields.Many2many("res.partner",
                                   string="Students")
    clinic_id = fields.Many2one("res.company",
                                string="Clinic",
                                copy=False,
                                default=lambda self: self.env[
                                    'res.company']._company_default_get())

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        """
            - Starting date must be prior to the ending date
        """
        for tt in self:

            # Starting date must be prior to the ending date
            start_date = tt.date_from
            end_date = tt.date_to
            if start_date and end_date and end_date < start_date:
                raise ValidationError(_('The ending date must not be prior\
                                                    to the starting date.'))

    def time_table_report_header(self, line):
        week_days = line.mapped(lambda l: l.week_day)
        return list(set(sorted(week_days)))

    def time_table_time_records(self, line):
        result_dict = {}
        domain_list = []
        for l in line:
            result_lines = line.read_group(
                domain=[('id', 'in', line.ids), ('time_to', '=', l.time_to),
                        ('timetable_id', '=', self.id)], fields=['time_from'],
                groupby=['time_from', 'time_to'])
            for result in result_lines:
                if not result.get('__domain') in domain_list:
                    domain_list.append(result.get('__domain'))
        for domain in domain_list:
            data = line.search(domain)
            for table in data:
                result_dict['{0:02.0f}:{1:02.0f}'.format(
                    *divmod(table.time_from * 60,
                            60)), '{0:02.0f}:{1:02.0f}'.format(
                    *divmod(table.time_to * 60, 60))] = dict(
                    zip(data.mapped('week_day'),
                        data.mapped(lambda l: str(l.activity_1 or '') + ',' +
                                    str(l.activity_2 or ''))))
        new_dict = OrderedDict(sorted(result_dict.items(), key=lambda l: l[0]))
        return new_dict


class TimeTableLine(models.Model):
    _name = 'time.table.line'
    _description = 'Time Table Line'

    Weeks = [
        ('1', 'Sunday'),
        ('2', 'Monday'),
        ('3', 'Tuesday'),
        ('4', 'Wednesday'),
        ('5', 'Thursday'),
        ('6', 'Friday'),
        ('7', 'Saturday'),
    ]
    time_from = fields.Float(string="Start Time")
    time_to = fields.Float(string="End Time")
    week_day = fields.Selection(selection=Weeks, string="Week day")
    activity_1 = fields.Char(string="Activity-1")
    activity_2 = fields.Char(string="Activity-2")
    timetable_id = fields.Many2one("time.table",
                                   string="Time Table")
