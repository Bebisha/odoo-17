# -*- encoding: utf-8 -*-
#
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
#


from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, date
from dateutil.relativedelta import relativedelta


class Partner(models.Model):
    _inherit = 'res.partner'


    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        recs = super(Partner, self).name_search(name, args, operator, limit)
        if self._context.get('from_group_appointment', False):
            if self._context.get('active_model') == 'group.appointment.booking':
                grp_app_booking_id = self.env[self._context.get('active_model')].browse(
                    self._context.get('active_id'))
                partner_ids = grp_app_booking_id.client_ids
                return partner_ids.name_get() if partner_ids.ids else recs
        return recs

    @api.constrains('dob')
    def _check_date(self):
        """
        Prevents the user to enter date of birth in the future
        """
        date_today = fields.Date.context_today(self)
        if self.dob and self.dob > date_today:
            raise ValidationError(_('The date of birth can not be future '
                                    'date.'))

    @api.depends('physician_ids')
    def _compute_physician(self):
        for rec in self:
            appointment_ids = self.env['appointment.appointment'].search([('client_id', '=', rec.id)])
            physician_ids = appointment_ids.mapped('physician_id')
            rec.physician_ids = physician_ids

    unique_no = fields.Char("Unique No")
    first_name = fields.Char(string='First Name', copy=False)
    last_name = fields.Char(string='Last Name', copy=False)
    middle_name = fields.Char(string='Middle Name', copy=False)
    is_physician = fields.Boolean(string="Is Physician")
    is_teacher = fields.Boolean(string="Is Teacher")
    is_student = fields.Boolean(string="Is Student")
    #     is_parent = fields.Boolean(string="Is Parent")
    is_employee = fields.Boolean(string="Is Employee")
    is_sponsor = fields.Boolean(string="Is Sponsor")

    physician_code_id = fields.Many2one("physician.code",
                                        string="Physician Code")
    position = fields.Char(string="Position")
    room_id = fields.Many2one("room.room",
                              string="Room")
    classroom_id = fields.Many2one("school.classroom",
                                   string="ClassRoom")
    account_payment_id = fields.Many2one('account.payment',
                                         string='Account PAyment')

    dob = fields.Date(string="Date of Birth")
    joining_date = fields.Date(string="Joining Date")
    physician_ids = fields.Many2many("res.partner",
                                     relation="partner_physican_rel",
                                     column1="partner_id",
                                     column2="physician_id",
                                     string="Seen By",
                                     compute='_compute_physician',
                                     search='_seen_by_search')

    observation_form_count = fields.Integer(
        compute="_compute_observation_form_count")
    physician_appointment_count = fields.Integer(
        compute="_compute_booked_appointment")
    client_appointment_count = fields.Integer(
        compute="_compute_client_appointment")
    client_group_app_count = fields.Integer(
        compute="_compute_client_appointment")

    service_type_ids = fields.Many2many('service.type', 'rec_id',
                                        string="Hibah Service Type")
    discount_service_type_ids = fields.Many2many('service.type',
                                                 string="Discount Service Type")

    hibah_percentage = fields.Float(string="Hibah fund Percentage(%)",
                                    tracking=True)
    dhf_received = fields.Selection([('yes', 'Yes'),
                                     ('no', 'No')], string="DHF Received",
                                    default='no')
    is_hf = fields.Boolean(string="HF")
    is_invoiceable = fields.Boolean(string="Is Invoiceable")
    fax = fields.Char(string="Fax")
    nationality_name = fields.Char(string="Nationality")
    emirates_id = fields.Char(string="Emirates ID", readonly=False, size=15)
    emiratesid_expiry = fields.Date(string="Emirates ID Expiry")
    emiratesid_expired = fields.Boolean(string="Emirates ID Expired",compute="_check_emirates_id_validity")
    age = fields.Float(string="Age", compute='compute_age')
    medium_id = fields.Many2one('appointment.medium', string="Medium")
    mode = fields.Selection([('sms', 'SMS'),
                             ('email', 'Email')], string="Communication Mode")
    gender = fields.Selection([('male', 'Male'),
                               ('female', 'Female'), ('other', 'Other')], string="Gender")
    father_name = fields.Char(string="Father Name")
    father_contact_no = fields.Char(string="Father Contact No")
    mother_name = fields.Char(string="Mother Name")
    mother_contact_no = fields.Char(string="Mother Contact No")
    cancel_appointment_count = fields.Integer(
        compute="_compute_cancel_appointment")
    rearrange_appointment_count = fields.Integer(
        compute="_compute_rearrange_appointment")
    client_payment_count = fields.Integer(
        compute="_compute_client_payment_count")
    vendor_payment_count = fields.Integer(
        compute="_compute_client_payment_count")
    partner_count_calls = fields.Integer(string="Total Calls",
                                         compute="_compute_partner_calls")
    partner_count_emails = fields.Integer(string="Total Emails",
                                          compute="_compute_partner_emails")
    partner_count_sms = fields.Integer(string="Total SMS",
                                       compute="_compute_partner_sms")
    payment_info = fields.Char(string='Payment Information')
    school_id = fields.Many2one('school.school', string="School ")
    tdcc_partner_id = fields.Integer(string="Partner TDCC ID")
    sponsor_rem_amt = fields.Float(
        compute="_compute_sponsor_payment")
    partner_count_attendance = fields.Integer(string="Total Attendance",
                                              compute="_compute_partner_attendance")
    physician_service_type_ids = fields.Many2many('service.type',
                                                  'physician_service_type_rel',
                                                  string='Physician Service Type')

    @api.onchange('is_hf')
    def _onchange_hf(self):
        for rec in self:
            if not rec.is_hf:
                rec.hibah_percentage = 0.0
                rec.service_type_ids = False

    def _seen_by_search(self, operator, value):
        """ Search method to filter Students based on physicians/seen by. """
        if operator in ('=', 'ilike') and value:
            if operator == 'ilike':
                value = "%" + value + "%"
            # retrieve all the physicians that match with a specific SQL query
            query = """select app.client_id
                        from appointment_appointment app
                        left join res_partner phy on app.physician_id = phy.id
                        where phy.name %s '%s' """ % (operator, value)
            self.env.cr.execute(query)
            ids = [t[0] for t in self.env.cr.fetchall()]
            return [('id', 'in', ids)]
        return []

    @api.depends()
    def _compute_partner_calls(self):
        MailMessage = self.env['mail.message'].sudo()
        lead_obj = self.env['crm.lead']
        mail_activity_type_id = self.env.ref('mail.mail_activity_data_call')
        for partner in self:
            domain = [('res_id', '=', partner.id),
                      ('model', '=', 'res.partner'),
                      ('mail_activity_type_id', '=', mail_activity_type_id.id)]
            messages_count = MailMessage.search_count(domain)
            lead_ids = lead_obj.search([('partner_id', '=', partner.id)])
            if lead_ids:
                domain1 = [('res_id', 'in', lead_ids.ids),
                           ('model', '=', 'crm.lead'),
                           ('mail_activity_type_id', '=', mail_activity_type_id.id)]
                messages_count += MailMessage.search_count(domain1)
            partner.partner_count_calls = messages_count

    @api.depends()
    def _compute_partner_attendance(self):
        attendance_obj = self.env['attendance.attendance']
        for partner in self:
            domain = [('student_id', '=', partner.id)]
            attendance_count = attendance_obj.search_count(domain)
            partner.partner_count_attendance = attendance_count

    @api.depends('emiratesid_expiry')
    def _check_emirates_id_validity(self):
        if self.emiratesid_expiry and self.emiratesid_expiry >= fields.Date.today():
            self.emiratesid_expired = False
        else:
            self.emiratesid_expired = True


    @api.depends()
    def _compute_partner_sms(self):
        Message = self.env['message.message'].sudo()
        for partner in self:
            domain = [('partner_ids', 'in', partner.ids)]
            sms_count = Message.search_count(domain)
            partner.partner_count_sms = sms_count

    @api.depends()
    def _compute_partner_emails(self):
        MailMail = self.env['mail.mail'].sudo()
        for partner in self:
            domain = [('recipient_ids', 'in', partner.ids)]
            if partner.email:
                domain = ['|', ('recipient_ids', 'in', partner.ids), (
                    'email_to', '=', partner.email)]
            email_count = MailMail.search_count(domain)
            partner.partner_count_emails = email_count

    def action_show_call_history(self):
        MailMessage = self.env['mail.message'].sudo()
        lead_obj = self.env['crm.lead']
        call_action = 'bista_tdcc_operations.action_mail_message_call_tdcc'
        call_action = self.env.ref(call_action).read()[0]
        mail_activity_type_id = self.env.ref('mail.mail_activity_data_call')
        domain = [('res_id', '=', self.id),
                  ('model', '=', 'res.partner'),
                  ('mail_activity_type_id', '=', mail_activity_type_id.id)]
        messages_ids = MailMessage.search(domain).ids
        lead_ids = lead_obj.search([('partner_id', '=', self.id)])
        if lead_ids:
            domain1 = [('res_id', 'in', lead_ids.ids),
                       ('model', '=', 'crm.lead'),
                       ('mail_activity_type_id', '=', mail_activity_type_id.id)]
            messages_ids += MailMessage.search(domain1).ids
        call_action['domain'] = [('id', 'in', list(set(messages_ids)))]
        return call_action

    def action_show_sms_history(self):
        Message = self.env['message.message'].sudo()
        sms_action = 'bista_sms_global.action_messages'
        sms_action = self.env.ref(sms_action).read()[0]
        sms_action['domain'] = [('partner_ids', 'in', self.ids)]
        sms_action['context'] = {'default_partner_ids': [(6, 0, self.ids)]}
        return sms_action

    def action_show_email_history(self):
        #         email_action = 'bista_tdcc_operations.action_mail_message_email_tdcc'
        email_action = 'bista_tdcc_operations.action_mail_mail_email_tdcc'
        action = self.env.ref(email_action).read()[0]
        action['display_name'] = _('Emails')
        domain = [('recipient_ids', 'in', self.ids)]
        if self.email:
            domain = ['|', ('recipient_ids', 'in', self.ids),
                      ('email_to', '=', self.email)]
        action['domain'] = domain
        return action

    @api.depends('dob')
    def compute_age(self):
        for partner in self:
            pass
            if partner.dob:
                today = date.today()
                birthday = datetime.strptime(
                    str(partner.dob), "%Y-%m-%d").date()
                diff = relativedelta(today, birthday)
                partner.age = diff.years
            else:
                self.age = 0.0

    @api.onchange('first_name', 'middle_name', 'last_name')
    def _onchange_names(self):
        for record in self:
            name_parts = []
            if record.first_name:
                name_parts.append(record.first_name)
            if record.middle_name:
                name_parts.append(record.middle_name)
            if record.last_name:
                name_parts.append(record.last_name)
            record.name = " ".join(name_parts)

    def _compute_client_payment_count(self):
        payment_obj = self.env['account.payment'].sudo()
        for partner in self:
            domain = [('partner_id', '=', partner.id),
                      ('payment_type', '=', 'inbound')]
            ven_domain = [('partner_id', '=', partner.id),
                          ('payment_type', '=', 'outbound')]
            partner.client_payment_count = payment_obj.search_count(
                domain)
            partner.vendor_payment_count = payment_obj.search_count(
                ven_domain)

    def _compute_sponsor_payment(self):
        acc_move_obj = self.env['account.move.line'].sudo()

        for sponsor in self:
            domain = [('partner_id', '=', sponsor.id)]
            sponsor_data = acc_move_obj.search(domain)
            total_debit = 0.0
            total_credit = 0.0
            for data in sponsor_data:
                total_debit += data.debit
                total_credit += data.credit
            rem_amt = total_debit - total_credit
            sponsor.sponsor_rem_amt = rem_amt

    def _compute_cancel_appointment(self):
        cancel_appointment_obj = self.env['common.cancellation']
        for partner in self:
            domain = [('client_id', '=', partner.id)]
            partner.cancel_appointment_count = \
                cancel_appointment_obj.search_count(domain)

    def show_sponsor_payment(self):
        sponsor_payment_action = 'bista_tdcc_operations.journal_item_action'
        action = self.env.ref(sponsor_payment_action).read()[0]
        for partner in self:
            domain = [('partner_id', '=', partner.id)]
            action['domain'] = domain
        return action

    def show_cancel_appointments(self):
        cancel_appointment_obj = self.env['common.cancellation']
        cancel_app_action = \
            'bista_tdcc_operations.appointment_common_cancel_action'
        action = self.env.ref(cancel_app_action).read()[0]
        for partner in self:
            domain = [('client_id', '=', partner.id)]
            CancelAppointmentRecs = cancel_appointment_obj.search(domain)
            if not CancelAppointmentRecs:
                return False
            if len(CancelAppointmentRecs) > 1:
                action['domain'] = [('id', 'in', CancelAppointmentRecs.ids)]
            elif CancelAppointmentRecs:
                cancel_appointment_form = \
                    'bista_tdcc_operations.common_cancellation_form'
                cancel_appointment_form_id = \
                    (self.env.ref(cancel_appointment_form).id, 'form')
                action['views'] = [cancel_appointment_form_id]
                action['res_id'] = CancelAppointmentRecs.id
        return action

    def _compute_rearrange_appointment(self):
        rearrange_appointment_obj = self.env['common.rearrangement']
        for partner in self:
            domain = [('client_id', '=', partner.id)]
            partner.rearrange_appointment_count = \
                rearrange_appointment_obj.search_count(domain)

    def show_rearrange_appointments(self):
        rearrange_appointment_obj = self.env['common.rearrangement']
        rearrange_appointment_action = \
            'bista_tdcc_operations.appointment_common_rearrangement_action'
        action = self.env.ref(rearrange_appointment_action).read()[0]
        for partner in self:
            domain = [('client_id', '=', partner.id)]
            RearrangeAppointmentRecs = rearrange_appointment_obj.search(domain)
            if not RearrangeAppointmentRecs:
                return False
            if len(RearrangeAppointmentRecs) > 1:
                action['domain'] = [('id', 'in', RearrangeAppointmentRecs.ids)]
            elif RearrangeAppointmentRecs:
                rearrange_appointment_form = \
                    'bista_tdcc_operations.common_rearrangement_form'
                rearrange_appointment_form_id = \
                    (self.env.ref(rearrange_appointment_form).id, 'form')
                action['views'] = [rearrange_appointment_form_id]
                action['res_id'] = RearrangeAppointmentRecs.id
        return action

    def _compute_client_appointment(self):
        appointmendt_obj = self.env['appointment.appointment']
        for partner in self:
            domain = [('client_id', '=', partner.id),
                      ('group_appointment_booking_id', '=', False),
                      ('state', '!=', 'cancelled')]
            domain_group = [('client_id', '=', partner.id),
                            ('group_appointment_booking_id', '!=', False),
                            ('state', '!=', 'cancelled')]
            partner.client_appointment_count = appointmendt_obj.search_count(
                domain)
            partner.client_group_app_count = appointmendt_obj.search_count(
                domain_group)

    def _compute_booked_appointment(self):
        appointmendt_obj = self.env['appointment.appointment']
        for partner in self:
            domain = [('physician_id', '=', partner.id)]
            partner.physician_appointment_count = appointmendt_obj. \
                search_count(domain)

    def _compute_observation_form_count(self):
        observation = self.env['observation.form'].sudo()
        for partner in self:
            domain = [('student_id', '=', partner.id)]
            partner.observation_form_count = observation.search_count(domain)

    def open_observation_form(self):
        Obseration = self.env['observation.form']
        observation_action = 'bista_tdcc_operations.observation_form_action'
        action = self.env.ref(observation_action).read()[0]
        for partner in self:
            domain = [('student_id', '=', partner.id)]
            ObservationRecs = Obseration.search(domain)
            if not ObservationRecs:
                return False
            if len(ObservationRecs) > 1:
                action['domain'] = [('id', 'in', ObservationRecs.ids)]
            elif ObservationRecs:
                form_observtion = 'bista_tdcc_operations.observation_form_form'
                observation_form = (self.env.ref(form_observtion).id, 'form')
                action['views'] = [observation_form]
                action['res_id'] = ObservationRecs.id
        return action

    def open_attendance(self):
        attendance_obj = self.env['attendance.attendance']
        attendance_action = 'bista_tdcc_operations.attendance_action_tdcc'
        action = self.env.ref(attendance_action).read()[0]
        for partner in self:
            domain = [('student_id', '=', partner.id)]
            attendance = attendance_obj.search(domain)
            if not attendance:
                return False
            if len(attendance) > 1:
                action['domain'] = [('id', 'in', attendance.ids)]
            elif attendance:
                form_attendance = 'bista_tdcc_operations.attendance_form_view_tdcc'
                attendance_form = (self.env.ref(form_attendance).id, 'form')
                action['views'] = [attendance_form]
                action['res_id'] = attendance.id
        return action

    def action_send_mail_partner(self):
        self.ensure_one()
        try:
            template_id = self.env.ref(
                'bista_tdcc_operations.accounts_kind_reminder_mail_template')
        except ValueError:
            template_id = False
        try:
            compose_form_id = self.env.ref(
                'mail.email_compose_message_wizard_form')
        except ValueError:
            compose_form_id = False
        ctx = {
            'default_model': 'res.partner',
            'default_res_ids': self.ids,
            'default_use_template': bool(template_id),
            'default_template_id': template_id and template_id.id,
            'default_composition_mode': 'comment',
            'default_mail_activity_type_id': self.env.ref(
                'mail.mail_activity_data_email').id,
            # 'custom_layout': "mail.mail_notification_borders",
            'force_email': True
        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id.id, 'form')],
            'view_id': compose_form_id.id,
            'target': 'new',
            'context': ctx,
        }
