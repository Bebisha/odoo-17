from odoo import models, fields, api, _
import random
import string


class PatientVisit(models.Model):
    _name = 'patient.visit'


    admission_type = fields.Many2one('admision.type',string="Admission Type")
    patient_class = fields.Many2one('patient.class',string="Patient Class")
    assigned_patient_location = fields.Char(string="Assigned Patient Location")
    patient_assigned_location_id = fields.Many2one('patient.assigned.location', string="Patient Assigned Location")
    first_name = fields.Char(string="First Name")
    middle_name = fields.Char(string="Middle Name")
    last_name = fields.Char(string="Last Name")
    mail_id = fields.Char(string="Email Address")
    visit_type = fields.Selection(
        [('O', 'Outpatient'),
         ('E', 'Emergency'),
         ('A', 'Admission'),
         ('B', 'Brief Encounter'),
         ('C', 'Consultation'),
         ('N', 'New (First visit)'),
         ('P', 'Post-operative')],
        string='Visit Type',default="O"
    )

    full_name = fields.Char(string="Physician", compute="_compute_full_name", store=True)
    patient_visit = fields.Char(string="Patient visit list", copy=False, index=True, readonly=False,
                                          default=lambda self: _('New'))

    hospital_service = fields.Many2one('hospital.service',string="Hospital Service")
    discharge_disposition_id = fields.Many2one('discharge.disposition', string="Discharge Disposition")


    patient_visit_id = fields.Many2one('appointment.appointment', string='Student')
    pv1_date = fields.Datetime('Last Update Date', default=lambda self: fields.Datetime.now())
    full_name = fields.Char(string="Attending Doctor", compute="_compute_full_name", store=True)

    @api.depends('first_name', 'middle_name', 'last_name', 'patient_visit_id.physician_id')
    def _compute_full_name(self):
        for record in self:
            if record.patient_visit_id:
                physician = record.patient_visit_id.physician_id  # Ensure this is fetching the related physician
                if physician:
                    record.last_name = physician.last_name or ''
                    record.middle_name = physician.middle_name or ''
                    record.first_name = physician.first_name or ''
                    record.full_name = f"{record.last_name} {record.middle_name}{record.first_name}".strip()
                else:
                    record.full_name = ''  # If no physician is found
            else:
                record.full_name = ''  # If no patient visit is found

    @api.model
    def create(self, vals):
        if vals.get('patient_visit', _('New')) == _('New'):
            vals['patient_visit'] = self.env['ir.sequence'].next_by_code(
                'patient_visit') or _('New')
        return super(PatientVisit, self).create(vals)
