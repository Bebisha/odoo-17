# -*- encoding: utf-8 -*-
#
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
#

from odoo import models, fields, api


class StudentPlan(models.Model):
    _name = 'student.plan'
    _description = 'Student Plan'

    # @api.multi
    def print_student_plan_report(self):
        return self.env.ref(
            'bista_tdcc_student_plan.action_student_plan_report'
            ).report_action(self)

    name = fields.Char(string="Name")
    plan_type = fields.Selection([('iep_intial_5_plus', 'IEP Initial 5+'),
                                  ('iep_intial', 'IEP Initial'),
                                  ('iep_summer', 'IEP Summer')],
                                 string="Plan Type")
    student_id = fields.Many2one('res.partner', string="Student")
    date_of_birth = fields.Date(string="Date of Birth")
    term_id = fields.Many2one('academic.term', string="Term")
    lead_educator_id = fields.Many2one('res.partner', string="Lead Educator")
    educator_id = fields.Many2one('res.partner', string="Educator")
    # parent_id = fields.Many2one('res.partner', string="Parent")
    director_educator_id = fields.Many2one('res.partner',
                                           string="Director Educator")
    date_produced = fields.Date(string="Date Produced")
    date_review = fields.Date(string="Date to be Reviewed")
    company_id = fields.Many2one('res.company',
                                 default=lambda self:
                                 self.env.user.company_id.id)
#
# IEP initial 5+, IEP Initial
    targets_comm = fields.Text(
        string="Targets (Communication and Language)")
    strategy_comm = fields.Text(
        string="Strategy (Communication and Language)")
    progress_comm = fields.Text(
        string="Progress (Communication and Language)")
    date_achieved_comm = fields.Date(
        string="Date Achieved (Communication and Language)")

    targets_moving = fields.Text(string="Targets (Moving and Handling)")
    strategy_moving = fields.Text(string="Strategy (Moving and Handling)")
    progress_moving = fields.Text(string="Progress (Moving and Handling)")
    date_achieved_moving = fields.Date(
        string="Date Achieved (Moving and Handling)")

    targets_health = fields.Text(string="Targets (Health and Self-Care)")
    strategy_health = fields.Text(string="Strategy (Health and Self-Care)")
    progress_health = fields.Text(string="Progress (Health and Self-Care)")
    date_achieved_health = fields.Date(
        string="Date Achieved (Health and Self-Care)")

    targets_confidence = fields.Text(
        string="Targets (Self-Confidence and Self-Awareness)")
    strategy_confidence = fields.Text(
        string="Strategy (Self-Confidence and Self-Awareness)")
    progress_confidence = fields.Text(
        string='Progress (Self-Confidence and Self-Awareness)')
    date_achieved_confidence = fields.Date(
        string='Date Achieved (Self-Confidence and Self-Awareness)')

    targets_behavior = fields.Text(
        string='Targets (Managing Feelings and Behaviour)')
    strategy_behaviour = fields.Text(
        string="Strategy (Managing Feelings and Behaviour)")
    progress_behaviour = fields.Text(
        string="Progress (Managing Feelings and Behaviour)")
    date_achieved_behaviour = fields.Date(
        string="Date Achieved (Managing Feelings and Behaviour)")

    targets_relationship = fields.Text(string="Targets (Making Relationships)")
    strategy_relationship = fields.Text(
        string="Strategy (Making Relationships)")
    progress_relationship = fields.Text(
        string="Progress (Making Relationships)")
    date_achieved_relationship = fields.Date(
        string="Date Achieved (Making Relationships)")

    targets_reading = fields.Text(string="Targets (Reading)")
    strategy_reading = fields.Text(string="Strategy (Reading)")
    progress_reading = fields.Text(string="Progress (Reading)")
    date_achieved_reading = fields.Date(string="Date Achieved (Reading)")

    targets_writing = fields.Text(string="Targets (Writing)")
    strategy_writing = fields.Text(string="Strategy (Writing)")
    progress_writing = fields.Text(string="Progress (Writing)")
    date_achieved_writing = fields.Date(string="Date Achieved (Writing)")

    targets_number = fields.Text(string="Targets (Number)")
    strategy_number = fields.Text(string="Strategy (Number)")
    progress_number = fields.Text(string="Progress (Number)")
    date_achieved_number = fields.Date(string="Date Achieved (Number)")

    targets_measure = fields.Text(
        string="Targets (Shape, Space and Measure)")
    strategy_measure = fields.Text(
        string="Strategy (Shape, Space and Measure)")
    progress_measure = fields.Text(
        string="Progress (Shape, Space and Measure)")
    date_achieved_measure = fields.Date(
        string="Date Achieved (Shape, Space and Measure)")

    targets_people = fields.Text(string="Targets (People and Communities)")
    strategy_people = fields.Text(string="Strategy (People and Communities)")
    progress_people = fields.Text(string="Progress (People and Communities)")
    date_achieved_people = fields.Date(
        string="Date Achieved (People and Communities)")

    targets_world = fields.Text(string="Targets (The World)")
    strategy_world = fields.Text(string="Strategy (The World)")
    progress_world = fields.Text(string="Progress (The World)")
    date_achieved_world = fields.Date(string="Date Achieved (The World)")

    targets_technology = fields.Text(string="Targets (Technology)")
    strategy_technology = fields.Text(string="Strategy (Technology)")
    progress_technology = fields.Text(string="Progress (Technology)")
    date_achieved_technology = fields.Date(string="Date Achieved (Technology)")

    targets_media = fields.Text(
        string="Targets (Exploring Media and Materials)")
    strategy_media = fields.Text(
        string="Strategy (Exploring Media and Materials)")
    progress_media = fields.Text(
        string="Progress (Exploring Media and Materials)")
    date_achieved_media = fields.Date(
        string="Date Achieved (Exploring Media and Materials)")

    targets_imaginative = fields.Text(string="Targets (Being Imaginative)")
    strategy_imaginative = fields.Text(string="Strategy (Being Imaginative)")
    progress_imaginative = fields.Text(string="Progress (Being Imaginative)")
    date_achieved_imaginative = fields.Date(
        string="Date Achieved (Being Imaginative)")

    # IEP initial
    targets_listening = fields.Text(
        string="Targets (Early Learning Goal 1 - (LA))")
    strategy_listening = fields.Text(
        string="Strategy (Early Learning Goal 1 - (LA))")
    progress_listening = fields.Text(
        string="Progress (Early Learning Goal 1 - (LA))")
    date_achieved_listening = fields.Date(
        string="Date Achieved (Early Learning Goal 1 - (LA))")

    targets_understanding = fields.Text(
        string="Targets (Early Learning Goal 2 – Understanding (U))")
    strategy_understanding = fields.Text(
        string="Strategy (Early Learning Goal 2 – Understanding (U))")
    progress_understanding = fields.Text(
        string="Progress (Early Learning Goal 2 – Understanding (U))")
    date_achieved_understanding = fields.Date(
        string="Date Achieved (Early Learning Goal 2 – Understanding (U))")

    targets_speaking = fields.Text(
        string="Targets (Early Learning Goal 3 – Speaking (S))")
    strategy_speaking = fields.Text(
        string="Strategy (Early Learning Goal 3 – Speaking (S))")
    progress_speaking = fields.Text(
        string="Progress (Early Learning Goal 3 – Speaking (S))")
    date_achieved_speaking = fields.Date(
        string="Date Achieved (Early Learning Goal 3 – Speaking (S))")

    # IEP Summer
    service_group_id = fields.Many2one('service.group', string="Service Group")
    no_of_weeks = fields.Integer(string="No.of weeks")
    speech_therapist_id = fields.Many2one('res.partner',
                                          string="Speech Therapist/s")
    occupational_therapist_id = fields.Many2one('res.partner',
                                                string='Occupational'
                                                'Therapist/s')
    educator_ids = fields.Many2many('res.partner', string="Educators")
    build_confidence_points = fields.Text("Build Confidence Points")
    build_confidence_review = fields.Text("Build Confidence Review")
    improve_social_points = fields.Text("Improve Social Points")
    improve_social_review = fields.Text("Improve Social Review")
    develop_communication_points = fields.Text("Develop Communication Points")
    develop_communication_review = fields.Text("Develop Communication Review")
    enhance_attention_points = fields.Text("Enhance Attention Points")
    enhance_attention_review = fields.Text("Enhance Attention Review")
    recommended_next_step = fields.Text("Recommended Next Steps")
