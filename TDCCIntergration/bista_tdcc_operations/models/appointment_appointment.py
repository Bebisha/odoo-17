# -*- encoding: utf-8 -*-
#
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
#


from odoo import models, fields, api, tools, _
import datetime
# import odoo.addons.decimal_precision as dp
from odoo.exceptions import ValidationError, UserError
import warnings
import pytz
from dateutil import relativedelta
from datetime import timedelta



class IrModelAccess(models.Model):
    _inherit = 'ir.model.access'

    @api.model
    @tools.ormcache_context('self._uid', 'model', 'mode', 'raise_exception',
                            keys=('lang',))
    def check(self, model, mode='read', raise_exception=True):
        context = dict(self.env.context)
        user_id = self.env.user
        if user_id.has_group('bista_tdcc_operations.group_tdcc_practitioner') \
                and context.get('from_physician') and mode != 'read' \
                and model == 'appointment.appointment':
            return False
        if user_id.has_group('account.group_account_invoice') \
                and context.get('from_account') and mode != 'read' \
                and model == 'appointment.appointment':
            return False
        return super(IrModelAccess, self).check(
            model, mode, raise_exception=raise_exception)


def time_calculation(find_value):
    key_value = {
        '0': '00',
        '0166666667': '01',
        '03333333333': '02',
        '0333333333': '02',
        '05': '03',
        '06666666667': '04',
        '0666666667': '04',
        '08333333333': '05',
        '0833333333': '05',
        '1': '06',
        '11666666667': '07',
        '1166666667': '07',
        '13333333333': '08',
        '1333333333': '08',
        '15': '09',
        '16666666667': '10',
        '1666666667': '10',
        '1833333333': '11',
        '183333333': '11',
        '2': '12',
        '21666666667': '13',
        '2166666667': '13',
        '23333333333': '14',
        '2333333333': '14',
        '25': '15',
        '2666666667': '16',
        '266666667': '16',
        '28333333333': '17',
        '2833333333': '17',
        '3': '18',
        '31666666667': '19',
        '3166666667': '19',
        '333333333333': '20',
        '33333333333': '20',
        '3333333333': '20',
        '35': '21',
        '36666666667': '22',
        '3666666667': '22',
        '38333333333': '23',
        '3833333333': '23',
        '4': '24',
        '41666666667': '25',
        '4166666667': '25',
        '4333333333': '26',
        '433333333': '26',
        '45': '27',
        '46666666667': '28',
        '4666666667': '28',
        '48333333333': '29',
        '4833333333': '29',
        '5': '30',
        '5166666667': '31',
        '53333333333': '32',
        '5333333333': '32',
        '55': '33',
        '56666666667': '34',
        '5666666667': '34',
        '58333333333': '35',
        '5833333333': '35',
        '6': '36',
        '61666666667': '37',
        '6166666667': '37',
        '63333333333': '38',
        '6333333333': '38',
        '65': '39',
        '666666666667': '40',
        '66666666667': '40',
        '6666666667': '40',
        '6833333333': '41',
        '7': '42',
        '71666666667': '43',
        '7166666667': '43',
        '73333333333': '44',
        '7333333333': '44',
        '75': '45',
        '7666666667': '46',
        '766666667': '46',
        '78333333333': '47',
        '7833333333': '47',
        '8': '48',
        '81666666667': '49',
        '8166666667': '49',
        '833333333333': '50',
        '83333333333': '50',
        '8333333333': '50',
        '85': '51',
        '86666666667': '52',
        '8666666667': '52',
        '88333333333': '53',
        '8833333333': '53',
        '9': '54',
        '916666666667': '55',
        '91666666667': '55',
        '9166666667': '55',
        '9333333333': '56',
        '933333333': '56',
        '95': '57',
        '96666666667': '58',
        '9666666667': '58',
        '98333333333': '59',
        '9833333333': '59',
    }
    if find_value:
        values = key_value[find_value]
    return values


class AppointmentAppointment(models.Model):
    _name = 'appointment.appointment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Appointment'
    _order = 'start_date asc'
    _rec_name = 'display_name'

    @api.depends('name', 'client_id')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.name
            if rec.client_id:
                rec.display_name = f"{rec.name} - {rec.client_id.name}"

    display_name = fields.Char(compute='_compute_display_name')

    name = fields.Char(string="Number", copy=False, default='/', readonly=True)
    service_group_id = fields.Many2one('service.group', string="Service Group")
    service_type_domain_id = fields.Many2many('service.type', string='Service Type Domain',
                                              compute='_compute_service_type_domain_id')
    service_type_id = fields.Many2one('service.type', string="Service Type", store=True,
                                      domain="[('id', 'in', service_type_domain_id)]")
    appointment_type_domain_id = fields.Many2many('appointment.type', string='Appointment Type Domain',
                                                  compute='_compute_appointment_type_domain_id')
    communication_type = fields.Selection([
        ('mail', 'Mail'),
        ('sms', 'SMS')
    ], string="Communication Type", copy=False, default='mail')
    auto_reminder = fields.Boolean(string="Auto Reminder")
    client_id = fields.Many2one('res.partner',
                                string="Clients",
                                domain=[('is_student', '=',
                                         True)])
    attendant_id = fields.Many2one('res.partner',
                                   string="Attendant",
                                   domain=[('is_student', '=', True)])
    clinic_id = fields.Many2one('res.company',
                                string="Clinic",
                                copy=False,
                                default=lambda self: self.env[
                                    'res.company']._company_default_get())
    physician_id = fields.Many2one(
        'res.partner', domain=[
            ('is_physician', '=', True)], tracking=True)
    teacher_ids = fields.Many2many('res.partner', string="Teachers",
                                   domain=[('is_teacher', '=', True)],
                                   tracking=True)
    product_id = fields.Many2one('product.product', string='Price List',
                                 tracking=True)
    room_id = fields.Many2one('room.room', string="Room",
                              tracking=True, copy=False)
    price_subtotal = fields.Float(
        string='Amount',
        digits=(16, 2), readonly=True)
    appointment_type_id = fields.Many2one('appointment.type',
                                          string="Appointment Type",domain="[('id', 'in', appointment_type_domain_id)]",
                                          tracking=True)
    date = fields.Datetime(string='Date', default=fields.Datetime.now)
    start_date = fields.Datetime(string='Start Date',
                                 index=True, copy=False,
                                 default=fields.Datetime.now,
                                 tracking=True)
    end_date = fields.Date(string='End Date', index=True,
                           copy=False, tracking=True)
    duration = fields.Float(string="Duration", copy=False, default=1,
                            tracking=True)
    common_cancellation_ids = fields.One2many(
        'common.cancellation',
        'appointment_id',
        string='Days Cancelled',
        copy=False,
        readonly=True)
    common_rearrangement_ids = fields.One2many('common.rearrangement',
                                               'appointment_id',
                                               string='Days Rearrange',
                                               copy=False,
                                               readonly=True)
    state = fields.Selection([
        ('new', 'Draft'),
        ('confirmed', 'Confirm'),
        ('dna', 'DNA'),
        ('arrive', 'Arrived'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
        ('invoiced', 'Invoiced')
    ], string="State", copy=False, default='new', tracking=True)
    invoice_count = fields.Integer(
        string='Invoice Count',
        compute='_get_invoice_count',
        readonly=True)
    week_days_ids = fields.Many2many(
        'week.days',
        'week_days_appointment_rel',
        'appointment_id',
        'week_days_id',
        string="Comfort Days",
        copy=False,
        readonly=True)
    clinical_notes = fields.Text(string="Clinical Notes")
    is_recurring = fields.Boolean(string="Is Recurring")
    recurring_start_date = fields.Date(string="Recurring Start Date")
    recurring_end_date = fields.Date(string="Recurring End Date")
    interval = fields.Integer(string="Interval")
    recurring_id = fields.Many2one(
        'appointment.appointment',
        string="Recurring Id",
        copy=False,
        readonly=True)
    appointment_line_ids = fields.One2many('appointment.appointment',
                                           'recurring_id', string='Line',
                                           copy=False, readonly=True)
    credit = fields.Float(
        string="Balance",
        compute='_compute_balance',
        search='_appointment_credit_search'
        )
    invoice_id = fields.Many2one('account.move', string="Invoice Ref.")
    invoice_state = fields.Selection(
        related='invoice_id.state',
        string="Invoice State",

    )
    active = fields.Boolean(string="Active", default=True)
    sale_id = fields.Many2one('sale.order', string="Quotations")
    is_student_arrived = fields.Boolean(string="Is Student Arrived?")

    # Following fields used for only group appointment
    group_appointment_booking_id = fields.Many2one('group.appointment.booking')
    appointment_date = fields.Date(string="Appointment Date")
    start_time = fields.Float(string='Start Time', readonly=True)
    end_time = fields.Float(string='End Time', readonly=True)
    day = fields.Selection([('sun', 'Sunday'), ('mon', 'Monday'),
                            ('tue', 'Tuesday'), ('wed', 'Wednesday'),
                            ('thu', 'Thursday'), ('fri', 'Friday'),
                            ('sat', 'Saturday')], string='Day', readonly=True)
    cancel_reason_id = fields.Many2one('appointment.cancel.reason',
                                       string='Cancel Reason',
                                       readonly=True)
    rearrange_reason_id = fields.Many2one('appointment.rearrange.reason',
                                          string='Rearrange Reason',
                                          readonly=True)
    rearrange_date = fields.Date(string='Reschedule to', readonly=True)
    tdcc_appointment_id = fields.Integer(string="TDCC Appointment ID")
    payment_term_id = fields.Many2one('account.payment.term',
                                      string='Payment Term')
    program_type = fields.Selection([('360', '360'),
                                     ('eip', 'EIP')],
                                    default='360')
    mail_send_duration = fields.Integer(string='Day Duration')
    date_to = fields.Datetime(
        string='Appointment Date End', compute='_compute_date_to',
        readonly=False)
    hide_inv_btn = fields.Boolean(string='Hide Invocie Button', default=False,
                                  compute='compute_hide_invoice_btn')
    non_chargeable_reason = fields.Text(string="Non Chargeable Reason")
    is_chargeable = fields.Selection([('chargeable', 'Yes'),
                                      ('non_chargeable', 'No')],
                                     string="Is Chargeable",
                                     tracking=True)
    week_interval = fields.Integer(string="Week Interval", default=1)

    @api.constrains('start_date')
    def _check_past_start_date(self):
        company_id = self.env.user.company_id
        if company_id.day_closing_date and self.start_date.date() <= \
                company_id.day_closing_date.date():
            raise ValidationError(_('You can not create appointment till'
                                    ' %s as day has been closed')
                                  % company_id.day_closing_date.date())

    # @api.one
    @api.constrains('start_date', 'room_id')
    def check_room_availability(self):
        if self.room_id and not self.group_appointment_booking_id and \
                self.start_date:
            app_obj = self.env['appointment.appointment']
            domain = [('room_id', '=', self.room_id.id),
                      ('state', '!=', 'cancelled'),
                      ('id', '<>', self.id)]
            self_ids = app_obj.search(domain)
            start_date = self.start_date + datetime.timedelta(minutes=1)
            date_to = self.date_to - datetime.timedelta(minutes=1)
            for each in self_ids:
                if each.start_date and each.date_to and \
                        (each.start_date <= start_date <= each.date_to) or \
                        (each.start_date <= date_to <= each.date_to) or \
                        (start_date <= each.start_date <= date_to) or \
                        (start_date <= each.date_to <= date_to):
                    raise ValidationError(_(
                        '%s Room is already booked for the Appointment %s') % (
                                              self.room_id.name, each.name))

    @api.depends('start_date', 'duration')
    def _compute_date_to(self):
        for rec in self:
            if rec.duration and rec.start_date:
                rec.date_to = rec.start_date + timedelta(hours=rec.duration or 0.0)
            elif rec.start_date and not rec.duration:
                rec.date_to = rec.start_date
            else:
                rec.date_to = False

    def _notify_get_groups(self, message, groups):
        """ Give access button to users and portal customer as portal is integrated
        in sale. Customer and portal group have probably no right to see
        the document so they don't have the access button. """
        groups = super(AppointmentAppointment, self)._notify_get_groups(
            message, groups)
        self.ensure_one()
        for group_name, group_method, group_data in groups:
            group_data['has_button_access'] = False
        return groups

    @api.onchange('product_id')
    def onchange_product_id(self):
        if not self.product_id:
            return
        self.price_subtotal = self.product_id.lst_price or 0.00

    @api.onchange('is_chargeable')
    def onchange_is_chargeable(self):
        if self.is_chargeable == 'chargeable':
            self.non_chargeable_reason = False

    def _appointment_credit_search(self, operator, value):
        if operator not in ('<', '=', '>', '>=', '<='):
            return []
        query = """
                 SELECT
                     aml.partner_id,
                     sum(aml.debit) - sum(aml.credit) as balance
                 FROM
                     account_move_line aml
                     LEFT JOIN account_account aa
                     ON aml.account_id=aa.id

                 WHERE aa.account_type = 'asset_receivable' AND aml.parent_state = 'posted'
                 GROUP BY aml.partner_id
                 HAVING (sum(aml.debit) - sum(aml.credit)) %s %s""" % (operator,
                                                                       value)
        self._cr.execute(query)
        res = self._cr.fetchall()
        if not res:
            return [('id', '=', '0')]
        return [('client_id', 'in', [r[0] for r in res])]


    def _compute_balance(self):
        for bal in self:
            if bal.client_id:
                query = """
                            SELECT
                                sum(aml.debit) - sum(aml.credit) as balance
                            FROM
                                account_move_line aml
                                LEFT JOIN account_account aa
                                ON aml.account_id=aa.id
                            WHERE
                                aml.partner_id = %s
                                AND aml.parent_state = 'posted'
                                AND aa.account_type = 'asset_receivable' """ % bal.client_id.id
                self._cr.execute(query)
                result = self._cr.dictfetchall()
                if result:
                    bal.credit = result[0].get('balance')
                else:
                    bal.credit = 0.0
            else:
                bal.credit = 0.0

    @api.onchange('end_date')
    def onchange_end_date(self):
        if not self.start_date:
            raise UserError(_("Please enter start date first !"))
        if self.end_date and self.start_date and self.start_date.date() >= \
                self.end_date:
            raise UserError(_("End date should be greater than start date !"))

    @api.onchange('start_date')
    def onchange_start_date(self):
        if self.end_date and self.start_date.date() > self.end_date:
            raise UserError(
                _("Start date can not be greater than end date !"))

    """

    def delete_recurring_appointment(self):
        current_date = fields.Date.today()
        related_appointment = self.env['appointment.appointment'].search([
            ('recurring_id', '=', self.id)])
        if related_appointment:
            for appoint in related_appointment:
                if appoint.id != self.id:
                    if appoint.start_date.date() >= current_date \
                            and appoint.invoice_count == 0:
                        appoint.unlink()
        self.recurring_start_date = False
        self.recurring_end_date = False
        self.interval = 0
    """

    def get_time(self, date):
        d1 = datetime.datetime.strptime(
            str(date), '%Y-%m-%d %H:%M:%S')
        d1 = d1.replace(
            tzinfo=pytz.utc).astimezone(
            pytz.timezone(
                self.env.user.tz or 'UTC'))
        return "%s:%s" % (str(d1.hour), str(d1.minute))

    def action_dna(self):
        self.write({'state': 'dna'})


    def action_send_reminder_emails(self):
        """Send appointment reminder emails directly to clients."""
        if not self:
            raise UserError("No appointments selected to send reminder emails.")

        # Fetch the email template
        template = self.env.ref('bista_tdcc_operations.appointment_reminder_mail_template')

        if not template:
            raise UserError("The email template could not be found.")

        for appointment in self:
            if appointment.client_id and appointment.client_id.email:
                # Send the email for the specific appointment
                template.send_mail(appointment.id, force_send=True, raise_exception=True)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Emails Sent',
                'message': 'Appointment reminder emails have been sent successfully.',
                'type': 'success',
                'sticky': False,
            },
        }

    @api.model
    def send_mail_action(self):
        """Send Mail action logic."""
        template = self.env.ref('bista_tdcc_operations.appointment_reminder_mail_template')
        for appointment in self:
            if appointment.client_id and appointment.client_id.email:
                template.send_mail(appointment.id, force_send=True, raise_exception=True)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Emails Sent',
                'message': 'Appointment reminder emails have been sent successfully.',
                'type': 'success',
                'sticky': False,
            },
        }

    def action_send_appointment_mail(self):
        self.ensure_one()
        try:
            template_id = self.env.ref(
                'bista_tdcc_operations.appointment_reminder_mail_template')
        except ValueError:
            template_id = False
        try:
            compose_form_id = self.env.ref(
                'mail.email_compose_message_wizard_form')
        except ValueError:
            compose_form_id = False

        ctx = {
            'default_model': 'appointment.appointment',
            'default_res_ids': self.ids,
            'default_use_template': bool(template_id),
            'default_template_id': template_id and template_id.id,
            'default_composition_mode': 'comment',
            'default_partner_ids': [(6, 0, [self.client_id.id])],
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

    def action_set_to_draft(self):
        self.write({'state': 'new', 'is_student_arrived': False})

    def write(self, vals):
        public_holiday_obj = self.env['public.holidays']
        res = super(AppointmentAppointment, self).write(vals)
        for appointment in self:
            if appointment.group_appointment_booking_id:
                start_date = appointment.appointment_date
            else:
                start_date = appointment.start_date.date()
            is_public_holiday = public_holiday_obj.is_public_holiday(str(start_date), appointment.clinic_id.id)
            if is_public_holiday:
                raise UserError(_("Clinic is off on this scheduled date!"))
            if appointment.start_date and appointment.week_days_ids and appointment.end_date:
                comfort_days = []
                for days in appointment.week_days_ids:
                    comfort_days.append(days.name)
                if comfort_days and appointment.start_date.date().strftime('%a').lower() not in comfort_days:
                    raise UserError(_('The Start date has no week schedule. Either change the start date based on comfort days or add the day in comfort days.'))
        return res

    def action_reschedule_appointment(self):
        inv_obj = self.env['account.move']
        inv_state_active = False
        related_inv = inv_obj.search([('appointment_id', '=',
                                       self.id),
                                      ('state', '!=', 'cancel')])
        if related_inv:
            inv_state_active = True
        if self.invoice_count == 0 or not inv_state_active:
            return {
                'name': 'Rearrange Appointment',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'reschedule.appointment',
                'target': 'new',
                # 'context': {'appointment_id': self.id, 'child': False}

            }
        else:
            raise UserError(
                _("You can only Rearrange appointment if the invoice has not been raised or is in cancelled state!"))

    def action_additional_appointment_booking(self):
        return {
            'name': "Additional booking",
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'additional.booking',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def action_update_state_by_physician(self):
        return {
            'name': "Update State",
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'update.appointment.state',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def action_request_cancel(self):
        ctx = {'appointment_id': self.id}
        if self.end_date:
            ctx['default_with_end_date'] = True
        return {
            'name': "Cancel Reason",
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'appointment.cancel',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': ctx
        }

    def action_request_cancel_invoice(self):
        self.ensure_one()
        if self.invoice_id.state == 'cancel':
            raise UserError(_("Invoice already has been cancelled"))

    #         try:
    #             template_id = self.env.ref(
    #                 'bista_tdcc_operations.app_cancel_send_mail_template')
    #             compose_form_id = self.env.ref(
    #                 'mail.email_compose_message_wizard_form')
    #         except ValueError:
    #             template_id = compose_form_id = False
    #
    #         grp_id = self.env.ref('account.group_account_invoice')
    #         partner_ids = [user.partner_id.id for user in grp_id.users]
    #         ctx = {
    #             'default_model': 'appointment.appointment',
    #             'default_res_id': self.ids[0],
    #             'default_use_template': bool(template_id),
    #             'default_template_id': template_id and template_id.id,
    #             'default_composition_mode': 'comment',
    # 'custom_layout': "mail.mail_notification_borders",
    #             'force_email': True,
    #             'appointment': self.name,
    #             'client': self.client_id.name,
    #             'schedule_date': self.start_date,
    #             'invoice_no': self.invoice_id.number or False,
    #             'req_from': self.env.user.name,
    #             'default_partner_ids': [(6, 0, partner_ids)]
    #         }
    #         return {
    #             'type': 'ir.actions.act_window',
    #             'view_type': 'form',
    #             'view_mode': 'form',
    #             'res_model': 'mail.compose.message',
    #             'views': [(compose_form_id.id, 'form')],
    #             'view_id': compose_form_id.id,
    #             'target': 'new',
    #             'context': ctx,
    #         }

    def action_cancel(self):
        cancel_reason = self._context.get('reason')
        related_inv = self.env['account.move'].search([
            ('appointment_id', '=', self.id),
            ('state', '!=', 'cancel')])
        if related_inv:
            raise UserError(_("You can only cancel appointment if the invoice has not been raised or is in cancelled state!"))
        if self.group_appointment_booking_id:
            start_time = self.start_time
            end_time = self.end_time
            cancellation_date = self.appointment_date
        else:
            d1 = datetime.datetime.strptime(
                str(self.start_date), '%Y-%m-%d %H:%M:%S')
            d1 = d1.replace(tzinfo=pytz.utc).astimezone(pytz.timezone(
                self.env.user.tz or 'UTC'))
            d2 = d1 + datetime.timedelta(hours=self.duration)
            start_time = "%s.%s" % (str(d1.hour),
                                    str(d1.minute * 1666666667)) or 0.00
            end_time = "%s.%s" % (str(d2.hour),
                                  str(d2.minute * 1666666667)) or 0.00
            cancellation_date = self.start_date.date()
        vals = {
            'appointment_id': self.id or False,
            'group_appointment_booking_id':
                self.group_appointment_booking_id.id or False,
            'client_id': self.client_id.id or False,
            'date': cancellation_date,
            'cancel_id': cancel_reason.id or False,
            'day': cancellation_date.strftime('%a').lower() or '',
            'start_time': start_time,
            'end_time': end_time,
            'write_by_id': self._uid or self._uid.id,
            'physician_id': self.physician_id.id or False,
        }
        self.env['common.cancellation'].create(vals)
        self.write({'state': 'cancelled'})
        return True

    @api.constrains('start_date', 'end_date', 'week_days_ids')
    def _check_comfort_days(self):
        if self.start_date and self.end_date:
            comfort_days = []
            for days in self.week_days_ids:
                comfort_days.append(days.name)
            if comfort_days and self.start_date.date().strftime(
                    '%a').lower() not in comfort_days:
                raise UserError(
                    _("The Start date has no week schedule. Either change the start date based on comfort day or add the day in comfort days."))

    @api.model
    def create(self, vals):
        if vals.get('start_date', False):
            start_date = datetime.datetime.strptime(
                str(vals.get('start_date')), '%Y-%m-%d %H:%M:%S')
            date_start = start_date.replace(tzinfo=pytz.utc).astimezone(
                pytz.timezone(self.env.user.tz or 'UTC'))
            is_public_holiday = self.env['public.holidays'].is_public_holiday(
                str(date_start.date()), vals.get('clinic_id', False))
            if is_public_holiday:
                raise UserError(_("Clinic is off on this scheduled date!"))
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('appointment.appointment')
        res = super(AppointmentAppointment, self).create(vals)
        if res.start_date and res.week_days_ids and res.end_date:
            comfort_days = []
            for days in res.week_days_ids:
                comfort_days.append(days.name)
            if comfort_days and res.start_date.date().strftime('%a').lower() not in comfort_days:
                raise UserError(
                    _("The Start date has no week schedule. Either change the start date based on comfort day or add the day in comfort days."))
        return res

    # @api.model
    # def create(self, vals):
    #     if vals.get('start_date', False):
    #         start_date = datetime.datetime.strptime(
    #             str(vals.get('start_date')), '%Y-%m-%d %H:%M:%S')
    #         date_start = start_date.replace(tzinfo=pytz.utc).astimezone(
    #             pytz.timezone(self.env.user.tz or 'UTC'))
    #         is_public_holiday = self.env['public.holidays'].is_public_holiday(
    #             str(date_start.date()),
    #             vals.get('clinic_id', False))
    #         if is_public_holiday:
    #             warnings.warn(_("Clinic is off on this scheduled date !"))
    #     if vals.get('name', '/') == '/':
    #         vals['name'] = self.env['ir.sequence'].next_by_code(
    #             'appointment.appointment')
    #     return super(AppointmentAppointment, self).create(vals)
    #     if res.start_date and res.week_days_ids and res.end_date:
    #         for days in res.week_days_ids:
    #             comfort_days.append(days.name)
    #         if comfort_days and res.start_date.date().strftime(
    #                 '%a').lower() not in comfort_days:
    #             warnings.warn(
    #                 _("The Start date has no week schedule. \n \
    #                     Either change the start date based on \
    #                     comfort day or add the day in comfort days."))
    #     if res:
    #         template = self.env.ref(
    #             'bista_tdcc_operations.appointment_notification_mail_template')
    #         self.env['mail.template'].browse(template.id).send_mail(
    #             res.id, force_send=True)

    @api.depends('service_group_id')
    def _compute_service_type_domain_id(self):
        for rec in self:
            rec.service_type_domain_id = False
            #     # res = {'domain': {'appointment_type_id':
            #     #                   [('id', 'in', [])]},
            #     #        'value': {'appointment_type_id': False}}
            if rec.service_group_id.service_type_ids:
                type_ids = rec.service_group_id.service_type_ids.ids
                rec.service_type_domain_id = [(6, 0, type_ids)]

    @api.depends('service_type_id')
    def _compute_appointment_type_domain_id(self):
        for rec in self:
            rec.appointment_type_domain_id = False
            #     # res = {'domain': {'appointment_type_id':
            #     #                   [('id', 'in', [])]},
            #     #        'value': {'appointment_type_id': False}}
            if rec.service_type_id.appointment_type_ids:
                type_ids = rec.service_type_id.appointment_type_ids.ids
                rec.appointment_type_domain_id = [(6, 0, type_ids)]


        #     domain = {'appointment_type_id': [('id', 'in', type_ids)]}
        #     res.update({'domain': domain})
        # return res

    # service_type_id = fields.Many2one('your.service.type.model', string='Service Type',
    #                                   compute='_compute_service_type_id', store=True)

    # @api.depends('service_group_id')
    # def _compute_service_type_id(self):
    #     for record in self:
    #         type_ids = record.service_group_id.service_type_ids.ids if record.service_group_id else []
    #         record.service_type_id = False if not type_ids else type_ids[0]

    @api.onchange('appointment_type_id')
    def change_appontment_type_id(self):
        if self.appointment_type_id:
            self.product_id = self.appointment_type_id.product_id.id
            if self.appointment_type_id.chargeable and \
                    self.appointment_type_id.price:
                self.price_subtotal = self.appointment_type_id.price
            else:
                self.price_subtotal = 0.0
            if self.appointment_type_id.service_type_id.classroom_id:
                self.room_id = self.appointment_type_id.service_type_id. \
                    classroom_id.id
            if self.appointment_type_id.service_type_id.physician_id.id:
                self.physician_id = self.appointment_type_id.service_type_id. \
                    physician_id.id
            if self.appointment_type_id.length:
                self.duration = self.appointment_type_id.length

    @api.model
    def appointment_mail(self):
        current_date = fields.Date.today()
        tomorrow_date = current_date + datetime.timedelta(days=1)
        template = self.env.ref(
            'bista_tdcc_operations.appointment_reminder_mail_template')
        domain = [('state', 'in', ['confirmed', 'invoiced']),
                  ('communication_type', '=', 'mail'),
                  ('auto_reminder', '=', True),
                  ('program_type', '=', '360')]
        domain_eip = [('state', 'in', ['confirmed', 'invoiced']),
                      ('communication_type', '=', 'mail'),
                      ('auto_reminder', '=', True),
                      ('program_type', '=', 'eip')]
        eip_app_ids = self.search(domain_eip)
        appointment_ids = self.search(domain)
        for appointment in appointment_ids.filtered(
                lambda appoint: appoint.start_date.date() == tomorrow_date):
            template.send_mail(appointment.id, force_send=True)
        for appn in eip_app_ids.filtered(
                lambda appo: appo.start_date.date() == current_date +
                             datetime.timedelta(days=appo.mail_send_duration)):
            template.send_mail(appn.id, force_send=True)

    @api.model
    def appointment_generate_invoice(self):
        current_date = fields.Date.today()
        tomorrow_date = current_date + datetime.timedelta(days=1)
        appointment_ids = self.search([('state', 'not in',
                                        ('draft', 'cancelled', 'dna')),
                                       ('invoice_id', '=', False)])
        for apt in appointment_ids:
            if apt.start_date.date() == tomorrow_date:
                apt.action_create_invoice()

    def action_student_arrive(self):
        for appointment in self:
            appointment.write({'state': 'arrive',
                               'is_student_arrived': True})
        return True

    def action_appointment_confirm(self):
        for appointment in self:
            if not appointment.service_group_id:
                raise UserError(_('Missing data in Service Group!'))
            if not appointment.service_type_id:
                raise UserError(_('Missing data in Service Type!'))
            if not appointment.appointment_type_id:
                raise UserError(_('Missing data in Appointment Type!'))
            if not appointment.product_id:
                raise UserError(_('Missing data in Price List!'))
            if not appointment.physician_id:
                raise UserError(_('Missing data in Physician!'))
            if not appointment.start_date:
                raise UserError(_('Missing data in Start Date!'))
            if appointment.end_date:
                # if not appointment.appointment_line_ids:
                appointment.generate_comfort_days()
                # for line in appointment.appointment_line_ids:
                #     line.write({'state': 'confirmed'})
                # else:
                for line in appointment.appointment_line_ids:
                    if line.state == 'new':
                        line.write({'state': 'confirmed'})
            appointment.write({'state': 'confirmed'})
        return True

    def generate_comfort_days(self):
        week_list = []
        holiday_obj = self.env['public.holidays']
        if not self.start_date and not self.end_date:
            raise UserError(
                _('Without start date and end date, the whole schedule list can be generated!'))
        if not self.week_days_ids:
            raise UserError(_('Without days, can not process.'))
        for days in self.week_days_ids:
            week = {'day': days.name}
            week_list.append(week)
        if self.start_date and self.end_date:
            d1 = datetime.datetime.strptime(
                str(self.start_date)[:10], '%Y-%m-%d')
            d2 = datetime.datetime.strptime(str(self.end_date), '%Y-%m-%d')
            entry_date = datetime.datetime.strptime(
                str(self.start_date), '%Y-%m-%d %H:%M:%S')
            flag = 0
            if not self.appointment_line_ids:
                i = 0
            else:
                i = len(self.appointment_line_ids.ids)
            start_week = int(d1.strftime('%U'))
            while d1 <= d2:
                create_app = False
                holiday_sea = holiday_obj.search([('date', '=', str(
                    d1.date())), ('clinic_id', '=', self.clinic_id.id)])
                if not holiday_sea:
                    # Check for week interval and if week interval
                    if self.week_interval > 1:
                        current_week = int(d1.strftime('%U'))
                        week_diff = start_week - current_week
                        week_mod = week_diff % self.week_interval
                        if week_mod == 0:
                            create_app = True
                    else:
                        create_app = True
                    for week in week_list:
                        if d1.strftime('%a').lower() == week['day'] and \
                                not str(d1.date()) == str(
                                    datetime.datetime.strptime(str(
                                        self.start_date)[:10], '%Y-%m-%d').date()):
                            existing_apt = self.search(
                                [('start_date', '=', entry_date),
                                 ('client_id', '=', self.client_id.id),
                                 ('clinic_id', '=', self.clinic_id.id),
                                 ('state', '!=', 'cancelled'),
                                 ('recurring_id', '=', self.id)])
                            if not existing_apt and create_app:
                                i += 1
                                self.env['appointment.appointment'].create({
                                    'recurring_id': self.id,
                                    'name': self.name + '/' + str(i) or '/',
                                    'attendant_id':
                                        self.attendant_id and self.attendant_id.id or False,
                                    'client_id': self.client_id.id or False,
                                    'start_date': entry_date,
                                    'duration': self.duration or 0.00,
                                    'service_group_id':
                                        self.service_group_id.id or False,
                                    'service_type_id':
                                        self.service_type_id.id or False,
                                    'appointment_type_id':
                                        self.appointment_type_id.id or False,
                                    'clinic_id': self.clinic_id.id or False,
                                    'physician_id': self.physician_id.id or False,
                                    'room_id': self.room_id.id or False,
                                    'product_id': self.product_id.id or False,
                                    'price_subtotal': self.price_subtotal or 0.00,
                                    'state': self.state or 'new'
                                })
                d1 = d1 + relativedelta.relativedelta(days=1)
                entry_date = entry_date + relativedelta.relativedelta(days=1)
                flag += 1
        return False

    def action_set_complete(self):
        self.discharge_event()
        for appointment in self:
            appointment.write({'state': 'done'})
        return True

    def compute_hide_invoice_btn(self):
        inv_obj = self.env['account.move']
        invoice_obj = self.env['account.move'].sudo()
        for rec in self:
            invoice_id = invoice_obj.search([
                ('appointment_id', '=', rec.id),
                ('state', '!=', 'cancel')])
            if invoice_id:
                rec.hide_inv_btn = True
            else:
                rec.hide_inv_btn = False

    def action_create_invoice(self):
        company_id = self.env.user.company_id
        inv_obj = self.env['account.move']
        team_id_360 = self.env.ref('bista_tdcc_operations.tdcc_team_360')
        invoice_obj = self.env['account.move'].sudo()
        user_obj = self.env['res.users'].sudo()
        for appointment in self:
            if appointment.group_appointment_booking_id:
                start_date = appointment.appointment_date
            else:
                start_date = appointment.start_date.date()
            if company_id.day_closing_date and start_date <= company_id.day_closing_date.date():
                raise ValidationError(_('You cannot create an invoice because the day has been closed.'))
            if appointment.is_chargeable == 'non_chargeable':
                raise UserError(
                    _('Appointment is Non-Chargeable! You cannot create an invoice for a Non-Chargeable Appointment.'))
            can_invoice_id = invoice_obj.search([
                ('appointment_id', '=', appointment.id),
                ('state', '=', 'cancel')])
            if can_invoice_id:
                appointment.hide_inv_btn = True
                raise UserError(
                    _('You cannot generate an invoice for this appointment as the invoice related to this appointment is already cancelled.'))
            invoice_id = invoice_obj.search([
                ('appointment_id', '=', appointment.id),
                ('state', '!=', 'cancel')])
            if invoice_id:
                appointment.hide_inv_btn = True
                raise UserError(_('Invoice already generated for this appointment!'))
            account = appointment.product_id.property_account_income_id or appointment.product_id.categ_id.property_account_income_categ_id
            if not account:
                raise ValidationError(_('Please define an income account for the product "%s" or its category "%s".') %
                                      (appointment.product_id.name, appointment.product_id.categ_id.name))
            fpos = appointment.client_id.property_account_position_id
            if fpos and account:
                account = fpos.map_account(account)
            name = appointment.product_id.name or ''
            if appointment.product_id.description_sale:
                name += '\n' + appointment.product_id.description_sale
            user_id = user_obj.search([('partner_id', '=', appointment.physician_id.id)], limit=1)
            tax_id = appointment.product_id.taxes_id or account.tax_ids or self.env.user.company_id.account_sale_tax_id
            vals = {
                'invoice_origin': appointment.name,
                'invoice_date': appointment.start_date.date(),
                'invoice_payment_term_id': appointment.payment_term_id.id if appointment.payment_term_id else None,
                'invoice_date_due': appointment.start_date.date() + timedelta(
                    days=30) if not appointment.payment_term_id else None,
                'partner_id': appointment.client_id.id,
                'payment_info': appointment.client_id.payment_info,
                'move_type': 'out_invoice',
                'state': 'draft',
                'appointment_id': appointment.id,
                'invoice_user_id': user_id.id or False,
                'user_id': user_id.id or False,
                'attendant_id': appointment.attendant_id and appointment.attendant_id.id,
                'invoice_line_ids': [(0, 0, {
                    'product_id': appointment.product_id.id,
                    'service_type_id': appointment.service_type_id.id,
                    'service_group_id': appointment.service_group_id.id,
                    'appointment_type_id': appointment.appointment_type_id.id,
                    'name': name,
                    'quantity': 1,
                    'display_type': 'product',
                    'price_unit': appointment.price_subtotal,
                    'account_id': account.id,
                    'tax_ids': [(6, 0, tax_id.ids)] if tax_id else [],
                })],
            }
            if company_id.partner_id:
                partner_bank_result = self.env['res.partner.bank'].search(
                    [('partner_id', '=', company_id.partner_id.id)], limit=1)
                if partner_bank_result:
                    vals.update({'partner_bank_id': partner_bank_result.id})
            if team_id_360:
                vals.update({'team_id': team_id_360.id})
            invoice_id = inv_obj.create(vals)
            if not (appointment.client_id.is_hf or
                    (
                            appointment.client_id.discount_service_type_ids and appointment.service_type_id.id in appointment.client_id.discount_service_type_ids.ids)):
                invoice_id.action_post()
            appointment.write({'state': 'invoiced', 'invoice_id': invoice_id.id})
        return True

    @api.depends()
    def _get_invoice_count(self):
        inv_obj = self.env['account.move']
        for appointment in self:
            inv_count = inv_obj.search(
                [('appointment_id', '=', appointment.id)]).ids
            if len(inv_count):
                appointment.invoice_count = len(inv_count)
            else:
                appointment.invoice_count = 0

    def action_view_appointment(self):
        action = self.env.ref(
            'bista_tdcc_operations.appointment_view_action').read()[0]
        action['views'] = [
            (self.env.ref('bista_tdcc_operations.appointment_appointment_form_views').id, 'form')]
        action['res_id'] = self.ids[0]
        return action

    def action_view_invoice(self):
        inv_obj = self.env['account.move']
        invoices = inv_obj.search([('appointment_id', '=', self.id)])
        action = self.env.ref('account.action_move_out_invoice_type').read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            action['views'] = [
                (self.env.ref('account.view_move_form').id, 'form')]
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action
