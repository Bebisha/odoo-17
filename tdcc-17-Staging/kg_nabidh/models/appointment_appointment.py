from email.policy import default

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError,UserError
import re



class AppointmentsAppointment(models.Model):
    _inherit = 'appointment.appointment'

    patient_visit_ids = fields.One2many('patient.visit', 'patient_visit_id',
                                        string='Patient Visit')
    diagnosis_information_ids = fields.One2many('diagnosis.information', 'diagnosis_information_id',
                                                string='Diagnosis Information')
    observations_ids = fields.One2many('observations.form', 'observations_id', string='Observations')
    observations_result_ids = fields.One2many('observation.request', 'observations_request_id', string='Observations Result')
    procedures_segment_ids = fields.One2many('procedures.segment', 'procedures_segment_id',
                                             string='Procedures Segment')
    allergy_information_ids = fields.One2many('patient.allergy.information', 'patient_allergy_id',
                                              string='Patient Allergy Information')
    problems_form_ids = fields.One2many('problems.form', 'problems_form_id',
                                                  string='Problems')
    common_order_ids = fields.One2many('common.order', 'common_order_id',
                                                  string='Common Order')
    pharmacy_order_ids = fields.One2many('pharmacy.order', 'pharmacy_order_id',
                                                  string='Pharmacy Order')
    transcription_document_ids = fields.One2many('transcription.document.header', 'transcription_document_id',
                                                 string='Transcription Document Header')
    nte_ids = fields.One2many('notes.comments', 'nte_id',
                                                 string='Notes Comments')

    admit_source = fields.Many2one('admit.source', string="Admit Source")
    bed_number = fields.Char(string="Bed Number")
    bed_number_id = fields.Many2one('bed.number',string="Bed Number")
    bed_type = fields.Selection(
        [('CAR', 'Cardiology'),
         ('MED', 'Medicine'),
         ('PUL', 'Pulmonary'),
         ('SUR', 'Surgery'),
         ('URO', 'Urology')],
        string='Bed Number', required=True,default='MED'
    )
    visit_number = fields.Char(string="Visit Number", required=True,default="1")
    sheryan_id = fields.Char(string="SHERYAN ID",related='physician_id.sheryan_id.name',required=True,size=8)
    # sheryan_id = fields.Char(string="SHERYAN ID", required=True)
    hospital_service = fields.Many2one('hospital.service',string="Hospital Service", required=True)
    is_checkin = fields.Boolean(string="IS Checkin",default=False,copy=False)
    is_checkout = fields.Boolean(string="IS Checkout",default=False,copy=False)
    state = fields.Selection([
        ('new', 'Draft'),
        ('confirmed', 'Confirm'),
        ('dna', 'DNA'),
        ('arrive', 'Arrived'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
        ('invoiced', 'Invoiced'),
        ('checkin', 'Checkin')
    ], string="State", copy=False, default='new')


    @api.constrains('sheryan_id')
    def _check_field_length(self):
        for record in self:
            if record.sheryan_id:
                if not record.sheryan_id.isdigit() or len(record.sheryan_id) != 8:
                    raise ValidationError("Your field must be exactly 8 digits long and contain only numbers.")
                if re.search(r'(\d)\1{3}', record.sheryan_id):
                    raise ValidationError("Your Field must not contain 4 consecutive identical numbers.")

    def action_checkin(self):

        nabidh_status = self.client_id.action_register('A04')
        self.message_post(body=f"A04(Checkin) request sent to NABIDH. Status: {nabidh_status}")
        self.is_checkin = True

    def discharge_event(self):
        nabidh_status = self.client_id.discharge_event('A03',appointment=self)
        self.message_post(body=f"A03(Discharge)  sent to NABIDH. Status: {nabidh_status}")
        self.is_checkin = False
        self.is_checkout = True

    def action_student_arrive(self):
        for appointment in self:
            appointment.write({'state': 'arrive',
                               'is_student_arrived': True})
            appointment.discharge_event()
        return True

    def action_dna(self):
        self.write({'state': 'dna'})
        self.discharge_event()

    def problem_record_pc1(self):
        nabidh_status = self.client_id.problem_record_pc1('PC1',appointment=self)
        self.message_post(body=f"PC1(Problem Record message) sent to NABIDH. Status: {nabidh_status}")

    def action_update(self):
        self.ensure_one()
        nabidh_status = self.client_id.action_update('A08',appointment=self)
        self.message_post(body=f"A08(Update) sent to NABIDH. Status: {nabidh_status}")

    def unsolicited_transmission_observation(self):
        self.ensure_one()
        nabidh_status = self.client_id.unsolicited_transmission_observation('R01',appointment=self)
        self.message_post(body=f"R01(Observation) sent to NABIDH. Status: {nabidh_status}")

    def action_vo4(self):
        self.ensure_one()
        nabidh_status = self.client_id.action_vo4('V04',appointment=self)
        self.message_post(body=f"V04(Vaccination message) sent to NABIDH. Status: {nabidh_status}")


class AppointmentsCancel(models.TransientModel):
    _inherit = 'appointment.cancel'

    def action_cancel_send(self):

        appo_obj = False
        # Group Appointment
        if self._context.get('active_model') == 'group.appointment.booking':
            appointment_booking_id = \
                self.env[self._context.get('active_model')].browse(
                    self._context.get('active_id'))
            self.action_cancel_group_appointment(appointment_booking_id)
            return True

        # Normal Appointment
        if 'appointment_id' in self._context:
            appo_obj = self.env['appointment.appointment'].browse(
                int(self._context.get('appointment_id')))
            nabidh_status = appo_obj.client_id.cancel_admit('A11',appointment=appo_obj)
            appo_obj.message_post(body=f"A11(Cancellation) sent to NABIDH. Status: {nabidh_status}")
            ctx = {'reason': self.cancel_reason_id,
                   'appointment': appo_obj.name,
                   'client': appo_obj.client_id.name,
                   'schedule_date': appo_obj.start_date,
                   }

            if appo_obj.end_date:
                appointment_line_ids = appo_obj.appointment_line_ids.filtered(
                    lambda l: l.state != 'cancelled')
                if self.from_date and self.to_date:
                    if appo_obj.start_date.date(
                    ) >= self.from_date and appo_obj.start_date.date(
                    ) <= self.to_date:
                        appo_obj.with_context(ctx).action_cancel()
                    for line in appointment_line_ids:
                        inv_state_active = False
                        related_inv = self.get_related_invoice(line)
                        if related_inv:
                            inv_state_active = True
                        if line.start_date.date() >= self.from_date and \
                                line. \
                                        start_date.date() <= self.to_date and \
                                line.start_date.date() > \
                                fields.Date.today():
                            if inv_state_active:
                                raise UserError(_("Please cancel invoice in order to cancel appointment."))
                            line.with_context(ctx).action_cancel()
                elif (self.from_date and not self.to_date):
                    if appo_obj.start_date.date(
                    ) >= self.from_date:
                        appo_obj.with_context(ctx).action_cancel()
                    for line in appointment_line_ids:
                        inv_state_active = False
                        related_inv = self.get_related_invoice(line)
                        if related_inv:
                            inv_state_active = True
                        if line.start_date.date() >= self.from_date and line. \
                                start_date.date() > \
                                fields.Date.today():
                            if related_inv:
                                raise UserError(_("Please cancel invoice in order to cancel appointment."))
                            line.with_context(ctx).action_cancel()
                elif (not self.from_date and self.to_date):
                    if appo_obj.start_date.date(
                    ) <= self.to_date:
                        appo_obj.with_context(ctx).action_cancel()
                    for line in appointment_line_ids:
                        inv_state_active = False
                        related_inv = self.get_related_invoice(line)
                        if related_inv:
                            inv_state_active = True

                        if line.start_date.date() <= self.to_date and line. \
                                start_date.date() > \
                                fields.Date.today():
                            if related_inv:
                                raise UserError(_("Please cancel invoice in order to cancel appointment."))
                            line.with_context(ctx).action_cancel()
                elif not self.from_date and not self.to_date:
                    appo_obj.with_context(ctx).action_cancel()
                    for line in appointment_line_ids:
                        inv_state_active = False
                        related_inv = self.get_related_invoice(line)
                        if related_inv:
                            inv_state_active = True
                            # raise Warning(_('Please cancel invoice in order '
                            #                 'to cancel appointment.'))
                            if line.invoice_count == 0 or not \
                                    inv_state_active:
                                line.with_context(ctx).action_cancel()
            else:
                appo_obj.with_context(ctx).action_cancel()

            """
            template = self.env.ref(
                'bista_tdcc_operations.appointment_cancellation_mail_template')
            ctx = {
                'reference': appo_obj.name,
                'send_to': ','.join(map(str, account_manager)),
                'client': appo_obj.client_id.name,
                'schedule_date': appo_obj.start_date,
            }
            self.env['mail.template'].browse(
                template.id).with_context(ctx).send_mail(
                self.id, force_send=True)
            """





class KGUpdateAppointmentState(models.TransientModel):
    _inherit = 'update.appointment.state'


    def update_state(self):
        context = dict(self.env.context)
        day_close_date = self.env.user.company_id.day_closing_date
        active_id = context.get('active_id')
        if active_id and \
                context.get('active_model') == 'appointment.appointment':
            appointment_id = self.env['appointment.appointment'].browse(
                active_id)
            app_start_date = appointment_id.start_date.date()
            if app_start_date <= day_close_date.date():
                raise ValidationError(_('Day is closed for appointment \
                                    date "%s"') %app_start_date)
            elif app_start_date > day_close_date.date():
                if self.state == 'arrive':
                    is_student_arrived = True
                else:
                    is_student_arrived = False
                appointment_id.write({
                    'state': self.state,
                    'is_student_arrived': is_student_arrived})
                appointment_id.discharge_event()
        return True
