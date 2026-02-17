# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, fields


class Observation(models.Model):
    _name = 'observation.form'
    _description = "Observation Form"

    name = fields.Char(string="name")
    student_id = fields.Many2one("res.partner",
                                 string="Child's Name")
    observation_no = fields.Integer(string="Observation No")
    date = fields.Date(string="Date", default=fields.Date.today)
    term_id = fields.Many2one("academic.term", string="Term")
    learning_observation = fields.Text(string="Learning Observation")
    child_significant = fields.Text(string="Child significant")
    general = fields.Text(string="General")
    communication = fields.Text(string="Communication")
    physical_dev_mh = fields.Text(string="Physical Development(MH)")
    physical_dev_hsc = fields.Text(string="Physical Development(HSc)")
    personal_dev = fields.Text(string="Personal Development")
    literacy = fields.Text(string="Literacy")
    mathematics = fields.Text(string="Mathematics")
    understanding_world = fields.Text(string="Understanding World")
    expressive_art_design = fields.Text(string="Expressive Art Design")
    parent_nurse_cmt = fields.Text(string="Parent Nurse Comments")
    achievement = fields.Text(string="Achievements")
    learning_priorities = fields.Text(string="Learning Priorities")
