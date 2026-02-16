from ast import literal_eval

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class EmployeeTrainingForm(models.Model):
    _name = "employee.training.form"
    _description = "Employee Training Form"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Reference")
    employee_id = fields.Many2one("hr.employee", string="Employee")
    type_of_course = fields.Many2one("training.course", string="Type of Course")
    training_from_date = fields.Datetime("From Date")
    training_to_date = fields.Datetime("To Date")
    air_ticket_request = fields.Boolean(string="Air Ticket Request", default=False)
    departure_date = fields.Date(string="Departure Date")
    return_date = fields.Date(string="Return Date")
    sector_from = fields.Char(string="Sector From")
    sector_to = fields.Char(string="Sector To")
    hotel = fields.Boolean(string="Hotel", default=False)
    remark = fields.Text(string="Order/Remarks")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approval', 'Waiting Approval'),
        ('lm_approved', 'Line Manager approved'),('hr_approved', 'HR Approved'),
        ('gm_approved', 'GM Approved'),
        ('confirm', 'Confirmed'),
        ('reject', 'Rejected'),
        ('cancel', 'Cancelled')], default='draft', tracking=True)
    is_request = fields.Boolean(default=False,copy=False)
    is_wait_lm = fields.Boolean(default=False,copy=False)
    is_wait_hr = fields.Boolean(default=False,copy=False)
    is_wait_gm = fields.Boolean(default=False,copy=False)
    is_approved = fields.Boolean(default=False,copy=False)
    requested_by = fields.Many2one('res.users', string="Requested By")
    line_manager = fields.Many2one('res.users', string="Line Manager")
    general_manager = fields.Many2one('res.users', string="General Manager")
    company_id = fields.Many2one(comodel_name='res.company', default=lambda self: self.env.user.company_id,
                                 string='Company')
    line_manager_id = fields.Many2one("res.users", string="Line Manager Approved",copy=False)
    general_manager_id = fields.Many2one("res.users", string="GM Approved",copy=False)
    hr_id = fields.Many2one("res.users", string="HR Approved",copy=False)

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('emp.training.seq')
        vals['is_request'] = True
        return super(EmployeeTrainingForm, self).create(vals)

    @api.onchange('training_from_date', 'training_to_date', 'departure_date', 'return_date')
    def check_dates(self):
        for rec in self:
            if rec.training_from_date and rec.training_to_date and rec.training_from_date > rec.training_to_date:
                raise ValidationError(_("The Training start date must be less than the Training end date"))

            if rec.departure_date and rec.return_date and rec.departure_date > rec.return_date:
                raise ValidationError(_("The departure date must be less than the return date"))

    def kg_request(self):
        lm_users = []

        lm_approve_users = self.env['ir.config_parameter'].sudo().get_param(
            'kg_mashirah_oil_purchase.line_manager_ids', False)

        if not lm_approve_users or lm_approve_users == '[]':
            raise ValidationError(_("Please Select Line Manager in Configuration"))

        hr_approve_users = self.env['ir.config_parameter'].sudo().get_param(
            'kg_mashirah_oil_purchase.hr_manager_ids', False)

        if not hr_approve_users or hr_approve_users == '[]':
            raise ValidationError(_("Please Select HR in Configuration"))


        gm_approve_users = self.env['ir.config_parameter'].sudo().get_param(
            'kg_mashirah_oil_purchase.general_manager_ids', False)

        if not gm_approve_users or gm_approve_users == '[]':
            raise ValidationError(_("Please Select General Manager in Configuration"))

        if literal_eval(lm_approve_users):
            for i in literal_eval(lm_approve_users):
                users = self.env['res.users'].browse(i)
                if users:
                    lm_users.append(users)

            for user in lm_users:
                self.activity_schedule('kg_mashirah_oil_hrms.line_manager_approval_notification',
                                       user_id=user.id,
                                       note=f' The User {self.env.user.name} request the Line Manager to approve the Employee Training Form {self.name}. Please Verify and approve.')

        self.is_wait_lm = True
        self.requested_by = self.env.user.id
        self.state = 'waiting_approval'

    def kg_lm_approve(self):
        lm_approve_users = self.env['ir.config_parameter'].sudo().get_param(
            'kg_mashirah_oil_purchase.line_manager_ids', False)

        if self.env.user.id not in literal_eval(lm_approve_users):
            raise UserError(_("You have no access to approve"))

        else:
            line_manager_notification_activity = self.env.ref(
                'kg_mashirah_oil_hrms.line_manager_approval_notification')

            activity_1 = self.activity_ids.filtered(lambda l: l.activity_type_id == line_manager_notification_activity)
            not_current_user_confirm = activity_1.filtered(lambda l: l.user_id != self.env.user)

            for ccc in not_current_user_confirm:
                ccc.unlink()

            activity_2 = self.activity_ids.filtered(
                lambda l: l.activity_type_id == line_manager_notification_activity)
            activity_2.action_done()

            hr_approve_users = self.env['ir.config_parameter'].sudo().get_param(
                'kg_mashirah_oil_purchase.hr_manager_ids', False)

            hr_users = []

            if literal_eval(hr_approve_users):
                for i in literal_eval(hr_approve_users):
                    users = self.env['res.users'].browse(i)
                    if users:
                        hr_users.append(users)

                for user in hr_users:
                    self.activity_schedule('kg_mashirah_oil_hrms.hr_approval_notification',
                                           user_id=user.id,
                                           note=f' The user {self.env.user.name} has approved the Line Manager approval and request the HR to approve the Employee Training Form {self.name}. Please Verify and approve.')

            self.is_wait_hr = True
            self.state = 'lm_approved'
            self.line_manager_id = self.env.user.id

    def kg_hr_approve(self):
        hr_approve_users = self.env['ir.config_parameter'].sudo().get_param(
            'kg_mashirah_oil_purchase.hr_manager_ids', False)
        if self.env.user.id not in literal_eval(hr_approve_users):
            raise UserError(_("You have no access to approve"))
        else:
            hr_notification_activity = self.env.ref(
                'kg_mashirah_oil_hrms.hr_approval_notification')
            activity_1 = self.activity_ids.filtered(
                lambda l: l.activity_type_id == hr_notification_activity)
            not_current_user_confirm = activity_1.filtered(lambda l: l.user_id != self.env.user)
            for ccc in not_current_user_confirm:
                ccc.unlink()

            activity_2 = self.activity_ids.filtered(
                lambda l: l.activity_type_id == hr_notification_activity)
            activity_2.action_done()

            gm_approve_users = self.env['ir.config_parameter'].sudo().get_param(
                'kg_mashirah_oil_purchase.general_manager_ids', False)

            gm_users = []

            if literal_eval(gm_approve_users):
                for i in literal_eval(gm_approve_users):
                    users = self.env['res.users'].browse(i)
                    if users:
                        gm_users.append(users)

                for user in gm_users:
                    self.activity_schedule('kg_mashirah_oil_hrms.general_manager_approval_notification',
                                           user_id=user.id,
                                           note=f' The user {self.env.user.name} has approved the HR approval and request the General Manager to approve the Employee Training Form {self.name}. Please Verify and approve.')

            self.is_wait_gm = True
            self.state = 'hr_approved'
            self.hr_id = self.env.user.id

    def kg_gm_approve(self):
        gm_approve_users = self.env['ir.config_parameter'].sudo().get_param(
            'kg_mashirah_oil_purchase.general_manager_ids', False)

        if self.env.user.id not in literal_eval(gm_approve_users):
            raise UserError(_("You have no access to approve"))

        else:
            general_manager_notification_activity = self.env.ref(
                'kg_mashirah_oil_hrms.general_manager_approval_notification')

            activity_1 = self.activity_ids.filtered(
                lambda l: l.activity_type_id == general_manager_notification_activity)
            not_current_user_confirm = activity_1.filtered(lambda l: l.user_id != self.env.user)

            for ccc in not_current_user_confirm:
                ccc.unlink()

            activity_2 = self.activity_ids.filtered(
                lambda l: l.activity_type_id == general_manager_notification_activity)
            activity_2.action_done()

            gm_approve_users = self.env['ir.config_parameter'].sudo().get_param(
                'kg_mashirah_oil_purchase.general_manager_ids', False)

            gm_users = []

            if literal_eval(gm_approve_users):
                for i in literal_eval(gm_approve_users):
                    users = self.env['res.users'].browse(i)
                    if users:
                        gm_users.append(users)

                for user in gm_users:
                    self.activity_schedule('kg_mashirah_oil_hrms.training_form_approval_notification',
                                           user_id=user.id,
                                           note=f' The user {self.env.user.name} has approved the General Manager approval of the Employee Training Form {self.name}.')

            training_approved_notification_activity = self.env.ref(
                'kg_mashirah_oil_hrms.training_form_approval_notification')

            activity_1 = self.activity_ids.filtered(
                lambda l: l.activity_type_id == training_approved_notification_activity)
            not_current_user_confirm = activity_1.filtered(lambda l: l.user_id != self.env.user)

            for ccc in not_current_user_confirm:
                ccc.unlink()

            activity_2 = self.activity_ids.filtered(
                lambda l: l.activity_type_id == training_approved_notification_activity)
            activity_2.action_done()

            self.state = 'gm_approved'
            self.is_approved = True
            self.general_manager_id = self.env.user.id
            self.kg_action_confirm()

    def kg_reject(self):
        if self.state == 'waiting_approval':
            lm_approve_users = self.env['ir.config_parameter'].sudo().get_param(
                'kg_mashirah_oil_purchase.line_manager_ids', False)

            if self.env.user.id not in literal_eval(lm_approve_users):
                raise UserError(_("You have no access to reject"))

        if self.state == 'lm_approved':
            gm_approve_users = self.env['ir.config_parameter'].sudo().get_param(
                'kg_mashirah_oil_purchase.general_manager_ids', False)

            if self.env.user.id not in literal_eval(gm_approve_users):
                raise UserError(_("You have no access to reject"))

        self.activity_schedule('kg_mashirah_oil_hrms.reject_employee_training_notification',
                               user_id=self.requested_by.id,
                               note=f' The user {self.env.user.name}  has rejected the approval of the Employee Training Form {self.name}.')

        reject_training_form_notification_activity = self.env.ref(
            'kg_mashirah_oil_hrms.reject_employee_training_notification')
        activity = self.activity_ids.filtered(
            lambda l: l.activity_type_id == reject_training_form_notification_activity)
        activity.action_done()

        line_manager_notification_activity = self.env.ref(
            'kg_mashirah_oil_hrms.line_manager_approval_notification')
        activity_1 = self.activity_ids.filtered(lambda l: l.activity_type_id == line_manager_notification_activity)
        activity_1.unlink()
        hr_notification_activity = self.env.ref(
                    'kg_mashirah_oil_hrms.hr_approval_notification')
        activity_1 = self.activity_ids.filtered(lambda l: l.activity_type_id == hr_notification_activity)
        activity_1.unlink()

        general_manager_notification_activity = self.env.ref(
            'kg_mashirah_oil_hrms.general_manager_approval_notification')
        activity_2 = self.activity_ids.filtered(lambda l: l.activity_type_id == general_manager_notification_activity)
        activity_2.unlink()

        self.state = 'reject'
        self.is_request = False
        self.is_wait_lm = False
        self.is_wait_gm = False
        self.is_approved = False

    def kg_cancel(self):
        self.state = 'cancel'
        self.is_request = False

    def kg_set_to_draft(self):
        self.state = 'draft'
        self.is_request = True
        self.is_wait_lm = False
        self.is_wait_gm = False
        self.is_approved = False

    def kg_action_confirm(self):
        self.state = 'confirm'
