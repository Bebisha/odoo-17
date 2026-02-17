# -*- coding: utf-8 -*-

import babel
from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta
from pytz import timezone

from odoo import api, fields, models, tools, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
import string
from calendar import monthrange




class DeductionApprovalSettings(models.Model):
    """ Extend model to add multilevel approval settings"""
    _name = 'deduction.approval.settings'

    name = fields.Char(string="Name")
    multi_level_validation = fields.Boolean(
        string='Enable Multiple Level Approval',
        help="If checked then multi-level approval is necessary")
    # leave_validation_type = fields.Selection(
    #     selection_add=[('multi', 'Multi Level Approval')])
    leave_validators = fields.One2many('deduction.approval.validators',
                                       'deduction_approval_status',
                                       string='Leave Validators',
                                       help="Leave validators")
    deduction_rule_id = fields.Many2one('hr.salary.rule', string="Salary Rule",
                                        domain=[('is_earn_deduct', '=', True),
                                                ('request_type','=','requestable')])

    # @api.onchange('leave_validation_type')
    # def enable_multi_level_validation(self):
    #     """ Enabling the boolean field of multilevel validation"""
    #     self.multi_level_validation = True if (
    #             self.leave_validation_type == 'multi') else False



class DeductionApprovalValidators(models.Model):
    """ Model for leave validators in Deduction approval settings configuration """
    _name = 'deduction.approval.validators'
    _order = 'sequence,id'

    deduction_approval_status = fields.Many2one('deduction.approval.settings')
    sequence = fields.Integer(default=10, help="Gives the sequence order when displaying a list of records.")

    deduction_validators = fields.Many2one('res.users',
                                         string='Validators',
                                         help="validators",
                                         domain="[('share','=',False)]")
    # level_of_approval = fields.Integer(string="Level of approval")
    approval_by = fields.Selection(
        [('coach', 'Hr Executive'), ('manager', 'Manager'), ('timeoff_officer', 'Time Off Officers'),('general_manager', 'General Manager'),
         ('hod', 'Head of Department'),('hr_dept','HR Dept')], string='Approval By', default='hod')




class DeductionApprovalStatus(models.Model):
    """ Model for leave validators and their status for each leave request """
    _name = 'deduction.approval.status'

    sequence = fields.Integer(default=10, help="Gives the sequence order when displaying a list of records.")

    deduction_status = fields.Many2one('hr.deduction')

    validating_users = fields.Many2one('res.users', string='Leave Validators',
                                       help="Leave validators",
                                       domain="[('share','=',False)]")
    validation_status = fields.Boolean(string='Approve Status', readonly=True,
                                       default=False,
                                       track_visibility='always', help="Status")
    leave_comments = fields.Text(string='Comments', help="Comments")
    # level_of_approval = fields.Integer(string="Level of approval")
    approval_by = fields.Selection(
        [('coach', 'Hr Executive'), ('manager', 'Manager'), ('timeoff_officer', 'Time Off Officers'),('general_manager', 'General Manager'),
         ('hod', 'Head of Department'),('hr_dept','HR Dept')], string='Approval By')

    @api.onchange('validating_users')
    def prevent_change(self):
        """ Prevent Changing leave validators from leave request form """
        raise UserError(_(
            "Changing leave validators is not permitted. You can only change "
            "it from Deduction Approval Settings"))