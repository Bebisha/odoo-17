import string

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, date
import random
from random import randrange
from dateutil.relativedelta import relativedelta
import requests
import json
import base64
import re


class Partner(models.Model):
    _inherit = 'res.partner'

    sending_facility = fields.Char(string="Sending Facility", compute='_compute_sending_facility')
    hide_peppol_fields = fields.Char()
    is_coa_installed = fields.Char()
    emirates_id = fields.Char(string="Emirates ID", size=15 ,copy=False,default=False)
    sheryan_id = fields.Many2one('sheryan.id',string="SHERYAN ID", size=8)



    @api.constrains('emirates_id')
    def _check_field_length(self):
        for record in self:
            if not record.emirates_id:
                raise ValidationError("Emirates ID is required.")
            if len(record.emirates_id) != 15:
                raise ValidationError("Emirates ID must be exactly 15 digits long.")
            if not record.emirates_id.isdigit():
                raise ValidationError("Emirates ID must contain only numbers.")

    @api.onchange('dob')
    def _onchange_emirates_id(self):
        if self.dob:
            # random_part = ''.join(random.choices(string.digits, k=8))
            self.emirates_id = "784" + str(self.dob.year)
        else:
            self.emirates_id = ''


    @api.depends('sending_facility')
    def _compute_sending_facility(self):
        get_param = self.env['ir.config_parameter'].sudo().get_param
        sending_facility = get_param('kg_nabidh.sending_facility')
        for record in self:
            if sending_facility:
                record.sending_facility = sending_facility
            else:
                record.sending_facility = "EMR"

    associated_parties_ids = fields.One2many('associated.parties', 'associated_parties_id', string='Associated Parties')

    guarantor_ids = fields.One2many('guarantor.form', 'guarantor_id', string='Guarantor')

    segment_family_history_ids = fields.One2many('segment.family.history', 'segment_family_history_id',
                                                 string='Segment Family History')
    segment_social_history_ids = fields.One2many('segment.social.history', 'segment_family_social_id',
                                                 string='Segment Social History')
    z_consent_ids = fields.One2many('z.segment.consent', 'segment_family_consent_id',
                                    string='Z Segment Consent')
    patient_identifer_ids = fields.One2many('patient.identification', 'patient_identification_id',
                                            string='PatientIdentification')

    insurance_ids = fields.One2many('insurance.form', 'insurance_id',
                                    string='Insurance')
    specimen_type_modifier_ids = fields.One2many('specimen.type.modifier', 'specimen_type_modifier_id',
                                                 string='Specimen Type')
    app_app_ids = fields.One2many('appointment.appointment', 'client_id',
                                  string='Appointment')
    state = fields.Char(string="state")

    attendant_id = fields.Char(string="state")
    msg_val = fields.Char(
        string="Message Type",

    )
    message_type = fields.Selection([
        ('A28', 'ADT^A28'),
        ('A03', 'ADT^A03'),
        ('A04', 'ADT^A04'),
        ('A08', 'ADT^A08'),
        ('A11', 'ADT^A11'),
        ('A31', 'ADT^A31'),
        ('A39', 'ADT^A39'),
        ('R01', 'ORU^R01'),
        ('T02', 'MDM^T02'),
        ('T08', 'MDM^T08'),
        ('PC1', 'PPR^PC1'),
        ('O01', 'ORM^O01'),
        ('V04', 'VXU^V04')
    ], string=" Message Type")

    date_message = fields.Datetime(string="Date/Time of Message", default=lambda self: fields.Datetime.now())

    nationality = fields.Many2one('nationality.form', string='Nationality')

    event_type_id = fields.Char(string='Event Type')

    event_date = fields.Datetime('Event Date', default=lambda self: fields.Datetime.now())

    is_send_Ao3 = fields.Boolean(string="IS Send A03", default=True)
    is_send_Ao4 = fields.Boolean(string="IS Send A04", default=True)
    is_send_Ao8 = fields.Boolean(string="IS Send A08", default=True)
    is_send_A11 = fields.Boolean(string="IS Send A11", default=True)
    is_send_A31 = fields.Boolean(string="IS Send A31", default=True)
    is_send_A39 = fields.Boolean(string="IS Send A39", default=True)
    is_vip_sent = fields.Boolean(string="IS VIP Send", default=False)
    is_vip = fields.Boolean(string="IS VIP Patient", default=False)
    is_global = fields.Boolean(string="IS Global", default=True)
    is_facility = fields.Boolean(string="IS Facility", default=True)
    is_merge = fields.Boolean(string="Merge record")
    link = fields.Char(compute='get_url', string='Nabidhu Url ')
    state = fields.Selection([('new', 'New'), ('register', 'Registered'), ('checkin', 'Chekin/New encounter'),
                              ('cancel', 'Cancel appoinment'), ('merger', 'Merger'), ('dischager', 'Discharge Event')],
                             string='Status', default='new')
    merge_record_ids = fields.Many2many('res.partner', relation='rec_id', string='Merge', compute='_compute_merge')

    mergr_ids = fields.One2many('merge.record', 'merge_id', string="Merge")

    @api.depends('merge_record_ids')
    def _compute_merge(self):
        for rec in self:
            appointment_ids = self.env['merge.record'].search([('patient_id', '=', rec.id)])
            physician_ids = appointment_ids.mapped('merge_patient_ids')
            rec.merge_record_ids = [
                (6, 0, physician_ids.ids)]

    def action_appoinment(self):
        return {
            'name': 'Appoinment',
            'res_model': 'appointment.appointment',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'domain': [('client_id', '=', self.id)],
            'target': 'current',

        }

    def action_appointment(self):
        self.ensure_one()
        reference_email = self.email
        if reference_email:
            matching_partners = self.env['res.partner'].search([
                ('email', '=', reference_email),
                ('id', '!=', self.id)
            ])
            if matching_partners:
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'merge.confirmation.wizard',
                    'view_mode': 'form',
                    'target': 'new',
                    'name': 'Merge Confirmation',
                    'context': {'default_student_id': self.id}
                }

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'appointment.appointment',
            'view_mode': 'form',
            'target': 'new',
            'name': 'Appointment',
            'context': {'default_client_id': self.id}
        }

    def action_merge(self):

        return {
            'name': 'Merge',
            'res_model': 'res.partner',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'domain': [('id', 'in', self.merge_record_ids.ids)],

        }

    def get_msh(self, message_type):

        return {

            "sendingApplication": "odoo",
            "sendingFacility": "TESTHOS20/TCODE10",
            "receivingFacility": "NABIDH",
            "destinationFacility": "DHA",
            "timestamp": self.date_message.strftime('%Y%m%d%H%M%S') if self.date_message else None,
            # "messageType": dict(self._fields['message_type']._description_selection(self.env)).get(message_type, '').split('^')[-1].strip(),
            "messageType": dict(self._fields['message_type']._description_selection(self.env)).get(message_type),
            "messageControlId": self.date_message.strftime('%Y%m%d%H%M%S') if self.date_message else None,
            "processingMode": "P",
            "version": "2.5",
            "encodingCharacters": "^~&",
            "characterSet": "UTF-8",
        }

    def get_evn(self, message_type):
        return {
            "eventType":  dict(self._fields['message_type']._description_selection(self.env)).get(message_type, '').split('^')[-1].strip(),
            "eventTimestamp": self.event_date.strftime('%Y%m%d%H%M%S') if self.event_date else None,
            "operator": {
                "id": "SHERYAN^7333258",
                "name": "SHERYAN"
            },
            "timestamp": self.event_date.strftime(
                '%Y%m%d%H%M%S') if self.event_date else None,
        }
    def get_evn_a08(self, message_type):
        return {
            "eventType":  dict(self._fields['message_type']._description_selection(self.env)).get(message_type, '').split('^')[-1].strip(),
            "eventTimestamp": self.event_date.strftime('%Y%m%d%H%M%S') if self.event_date else None,
            "operator": {
                "id": "SHERYAN^7333258",

            },
            # "timestamp": self.event_date.strftime(
            #     '%Y%m%d%H%M%S') if self.event_date else None,
        }

    def get_pid_a03(self, message_type):
        PID = {}
        for pat_iden in self.patient_identifer_ids:
            # for parties in self.associated_parties_ids:
            PID_a03 = {
                "mrn": pat_iden.patient_identifier_list,
                "emiratesId": self.emirates_id,
                "assigningAuthority": "TESTHOS20",
                "secondaryMrn": pat_iden.primary_lang.code + '^' + pat_iden.primary_lang.name + '^' + 'NAB024',
                "lastName": str(self.last_name) if self.last_name else '',
                "firstName": str(self.first_name) if self.first_name else '',
                "address": {
                    "city": str(self.city) if self.city else '',
                    "state": str(self.state_id.name) if self.state_id.name else '',
                    "zip": str(self.zip) if self.zip else '',
                    "country": str(self.country_id.name) if self.country_id.name else '',
                },
            }
            PID.update(PID_a03)

        return PID

    def get_pid(self, message_type):
        PID = {}

        for pat_iden in self.patient_identifer_ids:
            for parties in self.associated_parties_ids:
                pid = {
                    "patientID": pat_iden.patient_identifier_list,
                    "patientIdentifierList": [
                        "123456789",
                        "987654321"
                    ],
                    "name": {
                        "firstName": str(pat_iden.first_name) if pat_iden.first_name else '',
                        "lastName": str(pat_iden.last_name) if pat_iden.last_name else ''
                    },
                    "dateOfBirth": self.dob.strftime('%Y%m%d'),
                    "sex": pat_iden.administrative_sex.code,
                    "address": {
                        "streetAddress": str(parties.street) if parties.street else '',
                        "city": str(parties.city) if parties.city else '',
                        "state": str(parties.states.name) if parties.states.name else '',
                        "zip": str(parties.zip) if parties.zip else '',
                    },
                    "phoneNumber": self.mobile,

                }
                PID.update(pid)

        return PID

    def get_pid_pc1(self,message_type):
        PID = {}

        for pat_iden in self.patient_identifer_ids:
            # for parties in self.associated_parties_ids:
            pid = {
                "mrn": pat_iden.patient_identifier_list,
                "assigningAuthority": "TESTHOS20",
                "secondaryMrn": pat_iden.primary_lang.code + '^' + pat_iden.primary_lang.name + '^' + 'NAB024',
                "firstName": str(self.first_name) if self.first_name else '',
                "middleName": str(self.last_name) if self.last_name else '',
                # "gender": self.gender,
                "gender": next(iter(dict(self._fields['gender']._description_selection(self.env)).values()))[
                          :1].upper(),
                "dob": self.dob.strftime('%Y%m%d'),
                "address": {
                    "city": str(self.city) if self.city else '',
                    "state": str(self.state_id.name) if self.state_id.name else '',
                    "zip": str(self.zip) if self.zip else '',
                    "country": str(self.country_id.name) if self.country_id.name else '',
                },

                "phoneNumber": self.mobile,
                "phoneType": "PRN",
                "phoneNumberType": "CP",
                "maritalStatus": pat_iden.marital_status.code + '^' + pat_iden.marital_status.name + '^' + 'NAB002',
                "religion": pat_iden.religion.code + '^' + pat_iden.religion.name + '^' + 'NAB003',
                "citizenship": 'Emirati',
                "nationality": pat_iden.nationality.code,
                "otherDetails": "O",
                "datetimeOfMessage": pat_iden.pid_date.strftime('%Y%m%d%H%M%S') if pat_iden.pid_date else None,
            }
            PID.update(pid)

        return PID

    def get_pid_t02(self, message_type,appointment):
        PID = {}

        for pat_iden in self.patient_identifer_ids:

            pid = {
                "mrn": pat_iden.patient_identifier_list,
                "assigningAuthority": "TESTHOS20",
                "lastName": str(self.last_name) if self.last_name else '',
                "firstName": str(self.first_name) if self.first_name else '',
                "middleName": str(self.middle_name) if self.middle_name else '',
                "suffix": "D",
                 "gender": next(iter(dict(self._fields['gender']._description_selection(self.env)).values()))[:1].upper(),
                "dob": self.dob.strftime('%Y%m%d'),
                "address": {
                    "city": str(self.city) if self.city else '',
                    "state": str(self.state_id.name) if self.state_id.name else '',
                    "zip": str(self.zip) if self.zip else '',
                },
                "phoneNumber": {
                    "home": self.mobile
                },
                "secondaryMrn": pat_iden.primary_lang.code + '^' + pat_iden.primary_lang.name + '^' + 'NAB024',
                "maritalStatus": pat_iden.marital_status.code + '^' + pat_iden.marital_status.name + '^' + 'NAB002',
                "religion": pat_iden.religion.code + '^' + pat_iden.religion.name + '^' + 'NAB003',
                "emiratesId": self.emirates_id,
                #
                #
                #
                # "patientId": pat_iden.patient_identifier_list if pat_iden.patient_identifier_list else '',
                # "dateOfBirth": self.dob.strftime('%Y%m%d'),
                # "gender": pat_iden.administrative_sex.code,
                #
                # "name": {
                #     "firstName": str(self.first_name) if self.first_name else '',
                #     'GivenName': str(self.last_name) if self.last_name else '',
                #     "lastName": str(self.last_name) if self.last_name else '',
                # },
                # "address": {
                #     "streetAddress": str(self.street) if self.street else '',
                #     "city": str(self.city) if self.city else '',
                #     "state": str(self.state_id.name) if self.state_id.name else '',
                #     "zip": str(self.zip) if self.zip else '',
                # },
                # "phoneNumber": self.mobile,
            }
            PID.update(pid)
        return PID

    def get_pid_a04(self, message_type):
        PID = {}

        for pat_iden in self.patient_identifer_ids:
            # for parties in self.associated_parties_ids:
            pid = {
                "mrn": pat_iden.patient_identifier_list,
                "assigningAuthority": "TESTHOS20",
                "lastName": str(self.last_name) if self.first_name else '',
                "firstName": str(self.first_name) if self.first_name else '',
                "middleName": str(self.middle_name) if self.middle_name else '',
                # "gender": self.gender,
                "gender": next(iter(dict(self._fields['gender']._description_selection(self.env)).values()))[:1].upper(),
                "dob": self.dob.strftime('%Y%m%d'),
                "address": {
                    "city": str(self.city) if self.city else '',
                    "state": str(self.state_id.name) if self.state_id.name else '',
                    "zip": str(self.zip) if self.zip else '',
                },
                "emiratesId": self.emirates_id,
                "secondaryMrn": pat_iden.primary_lang.code + '^' + pat_iden.primary_lang.name + '^' + 'NAB024',
                "maritalStatus": pat_iden.marital_status.code,
                "religion": pat_iden.religion.code,
                "nationality": pat_iden.nationality.code,
                "language": pat_iden.primary_lang.code,
                "status": "O",
                "timestamp": pat_iden.pid_date.strftime('%Y%m%d%H%M%S') if pat_iden.pid_date else None,
                "facility": 'TESTHOS20',
                "phoneNumber": {
                    "home": self.mobile
                },
                "deathIndicator": pat_iden.patient_death_indicator,
                "unknownIndicator": pat_iden.identity_unknown_indicator,
                 "updatedTimestamp": datetime.now().strftime(
                    '%Y%m%d%H%M%S'),
                "updatedFacility": "TESTHOS20",
            }
            PID.update(pid)

        return PID

    def get_pid_a31(self, message_type):
        PID = {}

        for pat_iden in self.patient_identifer_ids:
            # for parties in self.associated_parties_ids:
            pid = {

                "mrn": pat_iden.patient_identifier_list,
                "assigningAuthority": "TESTHOS20",
                "patientName": {
                    "firstName": str(self.first_name) if self.first_name else '',
                    "middleName": str(self.last_name) if self.last_name else '',
                    "suffix": "D"
                },
                "dob": self.dob.strftime('%Y%m%d'),
                # "gender": self.gender,
                "gender": next(iter(dict(self._fields['gender']._description_selection(self.env)).values()))[:1].upper(),
                "address": {
                    "city": str(self.city) if self.city else '',
                    "state": str(self.state_id.name) if self.state_id.name else '',
                    "zip": str(self.zip) if self.zip else '',
                    "country": str(self.country_id.name) if self.country_id.name else '',
                },
                "phoneNumber": {
                    "home": self.mobile
                },
                "secondaryMrn": pat_iden.primary_lang.code + '^' + pat_iden.primary_lang.name + '^' + 'NAB024',
                "maritalStatus": pat_iden.marital_status.code + '^' + pat_iden.marital_status.name + '^' + 'NAB002',
                "religion": pat_iden.religion.code,
                "eid": self.emirates_id,
                "citizenship": "Emirati",
                "nationality": {
                    "codeSystem": pat_iden.nationality.code,
                }

            }
            PID.update(pid)

        return PID

    def get_pid_vo4(self, message_type):
        PID = {}

        for pat_iden in self.patient_identifer_ids:
            # for parties in self.associated_parties_ids:
            pid = {
                "mrn": pat_iden.patient_identifier_list,
                "emiratesId": self.emirates_id,
                "assigningAuthority": "TESTHOS20",
                "secondaryMrn": pat_iden.primary_lang.code + '^' + pat_iden.primary_lang.name + '^' + 'NAB024',
                # "lastName": str(pat_iden.last_name) if pat_iden.last_name else '',
                "firstName": str(self.first_name) if self.first_name else '',
                "middleName": str(self.last_name) if self.last_name else '',
                "address": {
                    "city": str(self.city) if self.city else '',
                    "state": str(self.state_id.name) if self.state_id.name else '',
                    "zip": str(self.zip) if self.zip else '',
                    "country": str(self.country_id.name) if self.country_id.name else '',
                },
                "dob": self.dob.strftime('%Y%m%d'),
                # "gender": self.gender,
                "gender": next(iter(dict(self._fields['gender']._description_selection(self.env)).values()))[:1].upper(),
                "maritalStatus": pat_iden.marital_status.code + '^' + pat_iden.marital_status.name + '^' + 'NAB002',
                "religion": pat_iden.religion.code + '^' + pat_iden.religion.name + '^' + 'NAB003',
            }
            PID.update(pid)

        return PID

    def get_pid_oo1(self, message_type):
        PID = {}

        for pat_iden in self.patient_identifer_ids:
            # for parties in self.associated_parties_ids:
            pid = {
                "mrn": pat_iden.patient_identifier_list,
                "emiratesId": self.emirates_id,
                "assigningAuthority": "TESTHOS20",
                "secondaryMrn": pat_iden.primary_lang.code + '^' + pat_iden.primary_lang.name + '^' + 'NAB024',
                "lastName": str(pat_iden.last_name) if pat_iden.last_name else '',
                "firstName": str(self.first_name) if self.first_name else '',
                "middleName":  str(self.last_name) if self.last_name else '',
                "address": {
                    "city": str(self.city) if self.city else '',
                    "state": str(self.state_id.name) if self.state_id.name else '',
                    "zip": str(self.zip) if self.zip else '',
                    "country": str(self.country_id.name) if self.country_id.name else '',
                },

            }
            PID.update(pid)

        return PID

    def get_pd1(self, message_type):
        PD1 = [""]
        return PD1

    def get_pd1_a11(self, message_type):
        # PD1 = {}
        PD1 = {
            "primaryCarePhysician": "Dr. Smith",
            "practice": "Metropolis Medical Center",
            "careTeam": [
                "Nurse Jane",
                "Therapist Mark"
            ]
        }
        return PD1

    def get_pd1_a04(self, message_type):
        # PD1 = {}
        PD1 = {
            "primaryCareProvider": {
                "id": "PCP123",
                "name": "Dr. Adam Lee"
            },
            "protectionIndicator": "N",
            "publicityIndicator": "Normal",
            "studentIndicator": "N",
            "livingArrangement": "Alone",
            "advanceDirectiveCode": "N"
        }
        return PD1

    # def get_pd1_a03(self, message_type):
    #     PD1 = {}
    #
    #     PD1: {
    #         "livingArrangement": "Alone",
    #         "publicityCode": "Normal",
    #         "protectionIndicator": "N",
    #         "studentIndicator": "N",
    #         "employmentStatus": "Active"
    #     }
    #     return PD1

    def get_pd1_a03(self, message_type):
        PD1 = {}
        for pat_iden in self.patient_identifer_ids:
            pid = {
                "livingArrangement": pat_iden.living_arrangement,
                "publicityCode": pat_iden.publicity_code,
                "protectionIndicator": pat_iden.protection_indicator,
                "studentIndicator": pat_iden.student_indicator,
                "employmentStatus": pat_iden.employment_status
            }
            PD1.update(pid)

        return PD1

    def get_nk1_ao3(self, message_type):
        NK1_03 = {}
        for parties in self.associated_parties_ids:
            nk1_a03 = {
                "relationship": parties.relationship.name,
                "name": {
                    "firstName": str(parties.first_name) if parties.first_name else '',
                    "lastName": str(parties.last_name) if parties.last_name else ''
                },
                "contactInfo": {
                    "phoneNumber": parties.phone_number,
                    "address": {
                        "streetAddress": str(parties.street) if parties.street else '',
                        "city": str(parties.city) if parties.city else '',
                        "state": str(parties.states.name) if parties.states.name else '',
                        "zip": str(parties.zip) if parties.zip else ''
                    }
                }
            }
            NK1_03.update(nk1_a03)
        return NK1_03

    def get_nk1(self, message_type):
        NK1 = []
        for parties in self.associated_parties_ids:
            nk1 = {

                "name": {
                    "familyName": str(parties.last_name) if parties.last_name else '',
                    "givenName": str(parties.first_name) if parties.first_name else '',
                    "middleName": str(parties.middle_name) if parties.middle_name else ''
                },
                "relationship": parties.relationship.name,
                "phone": parties.phone_number,

                # 'SetIDNK1': parties.set_id_nk1,
                # "SetName": {
                #     "FamilyName": str(parties.last_name) if parties.last_name else '',
                #     "GivenName": str(parties.first_name) if parties.first_name else '',
                #     "MiddleName": str(parties.middle_name) if parties.middle_name else ''
                # },
                # "Relationship": {
                #     "Identifier": parties.relationship.code,
                #     "Text": parties.relationship.name
                # },
                # "Address": {
                #     "StreetAddress": str(parties.street) if parties.street else '',
                #     "City": str(parties.city) if parties.city else '',
                #     "State": str(parties.states.name) if parties.states.name else '',
                #     "PostalCode": str(parties.zip) if parties.zip else '',
                #     "Country": str(parties.country.code) if parties.country.code else '',
                #     "AddressType": str(parties.addres_type.name) if parties.addres_type.name else ''
                # },
                # "ContactRole": {
                #     "Identifier": parties.emergency_contact.code,
                #     "Text": parties.emergency_contact.name
                # },
                #
                # 'PhoneNumber': parties.phone_number,
            }
            NK1.append(nk1)

        if not NK1:
            NK1 = [{}]

        return NK1

    def get_pv1_a04(self, message_type):
        PV1 = {}

        for app in self.app_app_ids:

            for patient in app.patient_visit_ids:
                for patient_vs in app.hospital_service:
                    pv1 = {
                        "visitNumber": app.visit_number if app.visit_number else '',
                        "class": patient.patient_class.name if patient.patient_class.name else '',
                        "facility": app.client_id.name,
                        "room": app.room_id.name if app.room_id.name else '',
                        "bed": 'PLS',
                        "admissionType": patient_vs.name,
                        "dischargeDisposition": patient.discharge_disposition_id.name if patient.discharge_disposition_id.name else '',
                        "admitSource": app.admit_source.name if app.admit_source.name else '',
                        "hospitalService": patient_vs.code,
                        "admitDate": app.start_date.strftime('%Y%m%d%H%M%S') if app.start_date else None,
                        "dischargeDate": patient.pv1_date.strftime('%Y%m%d%H%M%S') if patient.pv1_date else None,
                    }
                    PV1.update(pv1)

        return PV1

    def get_pv1_a11(self, message_type):
        PV1 = {}

        for app in self.app_app_ids:

            for patient in app.patient_visit_ids:
                for patient_vs in app.hospital_service:
                    pv1 = {
                        "class": patient.patient_class.name if patient.patient_class.name else '',
                        "assignedPatientLocation": patient.patient_assigned_location_id.code if patient.patient_assigned_location_id.code else '',
                    }
                    PV1.update(pv1)

        return PV1

    def get_pv1_r01(self, message_type,appointment):
        PV1 = {}

        for app in appointment:

            for patient in app.patient_visit_ids:
                # for patient_vs in app.hospital_service:
                pv1 = {
                    "visitNumber": app.visit_number if app.visit_number else '',
                    "visitType": patient.visit_type,
                     # for DHA we have SLT and OT Consultation.
                    "consultationType": "Consultation",
                    "room": app.room_id.name if app.room_id.name else '',
                    # "bed": 'PLS',
                    'visit': 'TCODE10',
                    'location': 'TESTHOS20',
                    "bed": 'PLS',
                    "attendingDoctor": {
                        "id": "00072892",
                        "lastName": app.physician_id.last_name if app.physician_id.last_name else '',
                        "firstName": app.physician_id.first_name if app.physician_id.first_name else '',
                        "middleName": app.physician_id.middle_name if app.physician_id.middle_name else '',
                        "title": "Dr.",
                        "operator": "SHERYAN"
                    }

                    # "patientClass": patient.patient_class.name if patient.patient_class.name else '',
                    # "assignedPatientLocation": patient.patient_assigned_location_id.code if patient.patient_assigned_location_id.code else '',
                    # "admissionType": patient_vs.name,
                    # "attendingDoctor": patient.full_name
                }
                PV1.update(pv1)

        return PV1

    def get_pv1_t02(self, message_type,appointment):
        PV1 = {}

        for app in appointment:

            for patient in app.patient_visit_ids:
                for patient_vs in app.hospital_service:
                    pv1 = {

                        "visitNumber": app.visit_number if app.visit_number else '',
                        "visitType": patient.visit_type,
                        "consultationType": "Consultation",
                        "room": app.room_id.name if app.room_id.name else '',
                        'location': 'TESTHOS20',
                        "bed": 'PLS',
                        "attendingDoctor": {
                        "id": "00072892",
                        "lastName": app.physician_id.last_name if app.physician_id.last_name else '',
                        "firstName": app.physician_id.first_name if app.physician_id.first_name else '',
                        "middleName": app.physician_id.middle_name if app.physician_id.middle_name else '',
                        "title": "Dr.",
                        "operator": "SHERYAN"
                    },
                        "visitStatus": "199",
                        "admitDate": app.start_date.strftime('%Y%m%d%H%M%S') if app.start_date else None,


                        # "patientID": patient.patient_visit,
                        # "patientClass": patient.patient_class.name if patient.patient_class.name else '',
                        # "attendingDoctor": {
                        #     "id": str(app.sheryan_id) if app.sheryan_id else '',
                        #     "name": {
                        #         "firstName": patient.first_name if patient.first_name else '',
                        #         "lastName": patient.last_name if patient.last_name else '',
                        #         "middleName": patient.middle_name if patient.middle_name else '',
                        #     }
                        # },
                        # "hospitalService": patient_vs.code
                    }
                    PV1.update(pv1)

        return PV1

    def get_pv1(self, message_type):
        PV1 = {}

        for app in self.app_app_ids:

            for patient in app.patient_visit_ids:
                for patient_vs in app.hospital_service:
                    pv1 = {
                        'patientClass': patient.patient_class.name if patient.patient_class.name else '',
                        'assignedPatientLocation': {
                            "facility": app.client_id.name,
                            "room": app.room_id.name,
                            "bed": 'PLS'

                        },
                        "attendingDoctor": {
                            "id": str(app.sheryan_id) if app.sheryan_id else '',
                            "name": {
                                "firstName": patient.first_name if patient.first_name else '',
                                "lastName": patient.last_name if patient.last_name else '',
                            }
                        },
                        'admissionType': patient_vs.name,
                        "dischargeDateTime": patient.pv1_date.strftime('%Y%m%d%H%M%S') if patient.pv1_date else None,
                    }
                    #     'SetIDPV1': "1",
                    #     'PatientClass': "O",
                    #     'AssignedPatientLocation': "Ambulatory Care",
                    #     'AdmissionType': "O",
                    #     "AttendingDoctor": {
                    #         "IdNumber": str(app.sheryan_id) if app.sheryan_id else '',
                    #         "FamilyName": patient.last_name if patient.last_name else '',
                    #         "GivenName": patient.first_name if patient.first_name else ''
                    #     },
                    #     "ConsultingDoctor": {
                    #         "IdNumber": str(app.sheryan_id) if app.sheryan_id else '',
                    #         "FamilyName": patient.last_name if patient.last_name else '',
                    #         "GivenName": patient.first_name if patient.first_name else ''
                    #     },
                    #     'HospitalService': patient_vs.code,
                    #     'AdmitSource': 'P',
                    #     'VisitNumber': app.visit_number,
                    #     'LastUpdateDateTime': app.start_date.strftime('%Y%m%d%H%M%S') if app.start_date else None,
                    #     'AdmitDateTime': app.start_date.strftime('%Y%m%d%H%M%S') if app.start_date else None,
                    #
                    # }

                    PV1.update(pv1)

        return PV1

    def get_pv1_pc1(self, message_type):
        PV1 = {}

        for app in self.app_app_ids:

            for patient in app.patient_visit_ids:
                for patient_vs in app.hospital_service:
                    pv1 = {

                        'SetIDPV1': "1",
                        'PatientClass': "O",
                        'AssignedPatientLocation': "Ambulatory Care",
                        'AdmissionType': "O",
                        "AttendingDoctor": {
                            "IdNumber": str(app.sheryan_id) if app.sheryan_id else '',
                            "FamilyName": patient.last_name if patient.last_name else '',
                            "GivenName": patient.first_name if patient.first_name else ''
                        },
                        "ConsultingDoctor": {
                            "IdNumber": str(app.sheryan_id) if app.sheryan_id else '',
                            "FamilyName": patient.last_name if patient.last_name else '',
                            "GivenName": patient.first_name if patient.first_name else ''
                        },
                        'HospitalService': patient_vs.code,
                        'AdmitSource': 'P',
                        'VisitNumber': app.visit_number,
                        'LastUpdateDateTime': app.start_date.strftime('%Y%m%d%H%M%S') if app.start_date else None,
                        'AdmitDateTime': app.start_date.strftime('%Y%m%d%H%M%S') if app.start_date else None,
                        'DischargeDateTime': app.start_date.strftime('%Y%m%d%H%M%S') if app.start_date else None
                    }

                    PV1.update(pv1)

        return PV1

    def get_pv1_A31(self, message_type,appointment):
        PV1 = {}

        for app in appointment:

            for patient in app.patient_visit_ids:
                # for patient_vs in app.hospital_service:
                pv1 = {
                    "visitNumber": app.visit_number,
                    "visitType": 'O',
                    'visit':'TCODE10',

                    # for DHA we have SLT and OT Consultation.
                    "consultationType": "Consultation",
                    "room": app.room_id.name if app.room_id else '',
                    "location": "TESTHOS20",
                    "priority": "O",
                    "bed": 'PLS',
                    "visitStatus": "199",
                    "admitDate": app.start_date.strftime('%Y%m%d%H%M%S') if app.start_date else None,
                    "attendingDoctor": {
                        "id": str(app.sheryan_id) if app.sheryan_id else '',
                        "lastName": patient.last_name if patient.last_name else '',
                        "firstName": patient.first_name if patient.first_name else '',
                        "middleName": patient.mail_id if patient.mail_id else '',
                        "title": "Dr.",
                        "operator": "SHERYAN"
                    },

                        # 'SetIDPV1': "1",
                        # 'PatientClass': "O",
                        # 'AssignedPatientLocation': "Ambulatory Care",
                        # 'AdmissionType': "O",
                        # "AttendingDoctor": {
                        #     "IdNumber": str(app.sheryan_id) if app.sheryan_id else '',
                        #     "FamilyName": patient.last_name if patient.last_name else '',
                        #     "GivenName": patient.first_name if patient.first_name else ''
                        # },
                        # "ConsultingDoctor": {
                        #     "IdNumber": str(app.sheryan_id) if app.sheryan_id else '',
                        #     "FamilyName": patient.last_name if patient.last_name else '',
                        #     "GivenName": patient.first_name if patient.first_name else ''
                        # },
                        # 'HospitalService': patient_vs.code,
                        # 'AdmitSource': 'P',
                        # 'VisitNumber': app.visit_number,
                        # 'LastUpdateDateTime': app.start_date.strftime('%Y%m%d%H%M%S') if app.start_date else None,
                        # 'AdmitDateTime': app.start_date.strftime('%Y%m%d%H%M%S') if app.start_date else None,
                        # 'DischargeDateTime': app.start_date.strftime('%Y%m%d%H%M%S') if app.start_date else None
                    }

                PV1.update(pv1)

        return PV1

    def get_pv1_ao3(self, message_type,appointment):
        PV1_A03 = {}

        for app in appointment:

            for patient in app.patient_visit_ids:
                # for patient_vs in app.hospital_service:
                pv1_a03 = {

                    "visitNumber": app.visit_number,
                    "visitType": patient.visit_type,
                    # for DHA we have SLT and OT Consultation.
                    "consultationType": "Consultation",
                    "room": app.room_id.name if app.room_id else '',
                    'visit': 'TCODE10',
                    'location': 'TESTHOS20',
                    "bed": 'PLS',

                    "attendingDoctor": (str(app.sheryan_id) if app.sheryan_id else '') + '^' + (
                        patient.first_name if patient.first_name else '') + '^' + (
                                           patient.last_name if patient.last_name else '') + '^' + (
                                           'email') + '^' + (str('Dr.')),

                }
                PV1_A03.update(pv1_a03)

        return PV1_A03

    def get_pv1_o01(self, message_type, appointment):
        PV1_A03 = {}

        for app in appointment:

            for patient in app.patient_visit_ids:
                # for patient_vs in app.hospital_service:
                pv1_a03 = {
                    "visitNumber": app.visit_number,
                    "visitType": patient.visit_type,
                    # for DHA we have SLT and OT Consultation.
                    "consultationType": "Consultation",
                    "room": app.room_id.name if app.room_id else '',
                    "bed": 'PLS',

                    "attendingDoctor": (str(app.sheryan_id) if app.sheryan_id else '') + '^' + (
                        patient.first_name if patient.first_name else '') + '^' + (
                                           patient.last_name if patient.last_name else '') + '^' + (
                                           'email') + '^' + (str('Dr.')),

                }
                PV1_A03.update(pv1_a03)

        return PV1_A03

    def get_pv2(self, message_type):
        PV2 = [""]
        return PV2

    def get_pv2_a03(self, message_type):
        # PV2 = {}
        PV2 = {
            "admitReason": "Severe abdominal pain",
            "patientValuables": [
                "Watch",
                "Wallet"
            ],
            "patientValuablesLocation": "Patient's Locker"
        }
        return PV2

    def get_spm_r01(self, message_type,appointment):
        SPM = {}
        for spm in self.specimen_type_modifier_ids:
            spms = {

                "specimenID": spm.specimen_id.name,
                "specimenType": spm.specimen_type_id.code,
                "specimenSource": 'NAB034',
            }
            SPM.update(spms)
        return SPM

    def get_tq1_r01(self, message_type):
        TQ1 = []
        for app in self.app_app_ids:
            for tq1q in app.common_order_ids:
                tq1 = {
                    "quantity": tq1q.quantity,
                    "interval": tq1q.interval,
                    "startDateTime": tq1q.start_date.strftime('%Y%m%d%H%M%S') if tq1q.start_date else None,
                    "endDateTime": tq1q.end_date.strftime('%Y%m%d%H%M%S') if tq1q.end_date else None,
                }
                TQ1.append(tq1)
        if not TQ1:
            TQ1 = [{}]
        return TQ1

    def get_obx_a04(self, message_type,appointment):
        OBX = []
        for app in appointment:
            for observation in app.observations_ids:
                obx = {
                    # "valueType": observation.value_type.code,
                    "valueType": 'NM',
                    "observationId": str(observation.ObservationIdentifier_units_id.code) + '^' + str(
                        observation.ObservationIdentifier_units_id.name)+'^'+'^'+'^'+'^'+'N',
                    "value": observation.observation_value,
                    "units": observation.units,
                    "abnormalFlags": observation.abnormal_flag_id.code,
                    "resultStatus": observation.observation_result_status.code,
                    "timestamp": app.date.strftime(
                        '%Y%m%d%H%M%S') if app.date else None,

                }
                OBX.append(obx)

            if not OBX:
                OBX = [{}]

            return OBX

    def get_obx(self, message_type, appointment):
        OBX = []
        for app in appointment:
            for observation in app.observations_ids:
                obx = {
                    "observationIdentifier": observation.ObservationIdentifier_units_id.code if observation.ObservationIdentifier_units_id else "" + '^' + observation.ObservationIdentifier_units_id.name + '^' + observation.value_type.code,
                    "observationValue": observation.observation_value,
                    "units": observation.units,
                    "normalRange": observation.references_range,
                }
                OBX.append(obx)

        if not OBX:
            OBX = [{}]

        return OBX

    def get_obx_a11(self, message_type):
        OBX = []
        for app in self.app_app_ids:
            for observation in app.observations_ids:
                obx = {

                    "setID": observation.set_id_obx,
                    "valueType": observation.value_type.name,
                    "observationIdentifier": observation.ObservationIdentifier_units_id.name,
                    "observationValue": observation.value_type.code,
                    "units": observation.units,
                    "observationSubID": "1"

                    # 'SetIDOBX': observation.set_id_obx,
                    # 'ValueType': observation.value_type.name,
                    # 'Units': observation.units,
                    # "ObservationIdentifier": {
                    #     "Identifier": observation.ObservationIdentifier_units_id.code,
                    #     "Text": observation.ObservationIdentifier_units_id.name
                    # },
                    #
                    # 'ObservationValue': observation.value_type.code,
                    # 'ObservationResultStatus': "N",
                    # 'DateTimeoftheObservation': app.date.strftime(
                    #     '%Y%m%d%H%M%S') if app.date else None,

                }
                OBX.append(obx)

        if not OBX:
            OBX = [{}]

        return OBX

    def get_obx_t02(self, message_type,appointment):
        OBX = []
        for app in appointment:
            for observation in app.observations_ids:
                base64_string = ''
                if observation.obs_atts:
                    base64_data = base64.b64encode(observation.obs_atts)

                    base64_string = base64_data.decode('utf-8')
                obx = {

                    "valueType": observation.value_type.code,
                    # "observationId":  "DS^Discharge Summary^NAB035",
                    "observationId": str(observation.observation_identifier.code) + '^' + str(
                        observation.observation_identifier.name) + '^' + 'NAB035',
                    "value": observation.observation_value,
                    "units": observation.units,
                    "abnormalFlags": observation.abnormal_flag_id.code,
                      "resultStatus": observation.observation_result_status.code,
                    "timestamp": app.date.strftime(
                        '%Y%m%d%H%M%S') if app.date else None,
                    "pdfData": base64_string

                    # 'SetIDOBX': observation.set_id_obx,
                    # 'ValueType': "ED",
                    # 'Units': observation.units,
                    # "ObservationIdentifier": {
                    #     "Identifier": "DS",
                    #     "Text": "Discharge Summary"
                    # },
                    #
                    # 'ObservationValue': base64_string,
                    # 'ObservationResultStatus': "F",
                    # 'DateTimeoftheObservation': app.date.strftime(
                    #     '%Y%m%d%H%M%S') if app.date else None,
                }
                OBX.append(obx)

        if not OBX:
            OBX = [{}]

        return OBX

    def get_obx_r01(self, message_type, ):
        OBX = []
        for app in self.app_app_ids:
            for observation in app.observations_ids:
                obx = {

                    "valueType": observation.observation_value,
                    "observationIdentifier": observation.ObservationIdentifier_units_id.name,
                    "observationValue": observation.observation_value_heart,
                    "units": observation.units,

                    # 'SetIDOBX': observation.set_id_obx,
                    # 'ValueType': "NM",
                    # 'Units': observation.units,
                    # "ObservationIdentifier": {
                    #     "Identifier": observation.ObservationIdentifier_units_id.code,
                    #     "Text": observation.ObservationIdentifier_units_id.name,
                    #     "NameOfCodingSytem": observation.ObservationIdentifier_units_id.code
                    # },
                    # "ReferencesRange": observation.ObservationIdentifier_units_id.value,
                    # 'ObservationValue': observation.observation_value_heart,
                    # 'ObservationResultStatus': observation.observation_result_status.code,
                    # 'DateTimeoftheObservation': app.date.strftime(
                    #     '%Y%m%d%H%M%S') if app.date else None,
                    # 'PerformingOrganizationName': observation.per_org_name,
                }

                OBX.append(obx)

        if not OBX:
            OBX = [{}]

        return OBX

    def get_al1(self, message_type,appointment):
        AL1 = []
        for app in appointment:
            for allergy_info in app.allergy_information_ids:
                al1 = {

                    "type": allergy_info.allergy_code_des.code if allergy_info.allergy_code_des else '',
                    "code": allergy_info.allergy_type_codes.code if allergy_info.allergy_type_codes else '',
                    "description": allergy_info.allergy_type_codes.name if allergy_info.allergy_type_codes else '',
                    "severity": allergy_info.allergy_severty_code.name if allergy_info.allergy_severty_code else '',
                    "onset": allergy_info.al1_date.strftime(
                        '%Y%m%d%') if allergy_info.al1_date else None
                }
                AL1.append(al1)

        if not AL1:
            AL1 = [{}]
        return AL1

    def get_vl_a03(self, message_type,appointment):
        VL = []
        for app in appointment:
            for patient in app.patient_visit_ids:
                for patient_vs in app.hospital_service:
                    vl = {
                        "code": "8287-5",
                        "description": "Head Circumference",
                        "value": "66",
                        "unit": "cm"

                    }
                    VL.append(vl)

        if not VL:
            VL = [{}]
        return VL

    def get_al1_a04(self, message_type,appointment):
        AL1 = []
        for app in appointment:
            for allergy_info in app.allergy_information_ids:
                typeDescription = allergy_info.allergy_code_des.name
                al1 = {
                    "type": allergy_info.allergy_code_des.code,
                    "typeDescription": typeDescription,
                    "typeCodeSystem": "NAB042",
                    "code": allergy_info.allergy_type_codes.code,
                    "codeDescription": allergy_info.allergy_type_codes.name,
                    "codeSystem": "NAB043",
                    "severity": allergy_info.allergy_severty_code.code,
                    "severityDescription": allergy_info.allergy_severty_code.name,
                    "severityCodeSystem": "HL7128",
                    "reaction": allergy_info.allergy_reaction_code.code,
                    "date": allergy_info.al1_date.strftime(
                        '%Y%m%d%H%M%S') if allergy_info.al1_date else None,

                    # 'SetIDAL1': allergy_info.set_id_al1,
                    # "AllergenTypeCode": {
                    #     "Identifier": allergy_info.allergy_type_codes.code,
                    #     "Text": allergy_info.allergy_type_codes.name
                    # },
                    # "AllergenCodeMnemonIcDescription": {
                    #     "Identifier": allergy_info.allergy_code_des.code,
                    #     "Text": allergy_info.allergy_code_des.name
                    # },
                    # "AllergySeverityCode": {
                    #     "Identifier": allergy_info.allergy_severty_code.code,
                    #     "Text": allergy_info.allergy_severty_code.name
                    # },
                    # 'AllergyReactionCode': allergy_info.allergy_reaction_code.code,
                    # 'IdentificationDate ': allergy_info.al1_date.strftime(
                    #     '%Y%m%d%H%M%S') if allergy_info.al1_date else None

                }
                AL1.append(al1)

        if not AL1:
            AL1 = [{}]
        return AL1

    def get_dg1(self, message_type):
        DG1 = []
        for app in self.app_app_ids:

            for diagnosis_info in app.diagnosis_information_ids:
                dg1 = {
                    "diagnosisCode": diagnosis_info.diag_code,
                    "diagnosisDescription": diagnosis_info.diag_description,
                    "diagnosisType": diagnosis_info.diag_type.name

                    # 'SetIDDG1': diagnosis_info.set_id_dg1,
                    # "DiagnosisCodeDG1": {
                    #     "Identifier": diagnosis_info.diag_code,
                    #     "Text": diagnosis_info.diag_description
                    # },
                    # 'DiagnosisDescription': diagnosis_info.diag_description,
                    # 'DiagnosisDateTime': diagnosis_info.dg1_date.strftime(
                    #     '%Y%m%d%H%M%S') if diagnosis_info.dg1_date else None,
                    # 'DiagnosisType': diagnosis_info.diag_type.code,
                    # 'DiagnosisPriority': diagnosis_info.diag_priority,
                    # 'DiagnosisActionCode': diagnosis_info.diag_action_code,
                    # 'DiagnosisCodingMethod': diagnosis_info.diagnosis_coding_method
                }

                DG1.append(dg1)

        if not DG1:
            DG1 = [{}]
        return DG1

    def get_dg1_a04(self, message_type):
        DG1 = []
        for app in self.app_app_ids:

            for diagnosis_info in app.diagnosis_information_ids:
                dg1 = {
                    "code": diagnosis_info.diag_code,
                    "description": diagnosis_info.diag_description,
                    "type": diagnosis_info.diag_type.name

                    # 'SetIDDG1': diagnosis_info.set_id_dg1,
                    # "DiagnosisCodeDG1": {
                    #     "Identifier": diagnosis_info.diag_code,
                    #     "Text": diagnosis_info.diag_description
                    # },
                    # 'DiagnosisDescription': diagnosis_info.diag_description,
                    # 'DiagnosisDateTime': diagnosis_info.dg1_date.strftime(
                    #     '%Y%m%d%H%M%S') if diagnosis_info.dg1_date else None,
                    # 'DiagnosisType': diagnosis_info.diag_type.code,
                    # 'DiagnosisPriority': diagnosis_info.diag_priority,
                    # 'DiagnosisActionCode': diagnosis_info.diag_action_code,
                    # 'DiagnosisCodingMethod': diagnosis_info.diagnosis_coding_method
                }

                DG1.append(dg1)

        if not DG1:
            DG1 = [{}]
        return DG1

    def get_drg_a03(self, message_type):
        DRG = {}
        for app in self.app_app_ids:
            for diagnosis_info in app.diagnosis_information_ids:
                drg = {  # Create the dictionary for each diagnosis
                    "drgCode": "470",
                    "drgDescription": "Major Joint Replacement or Reattachment of Lower Extremity without Major Complications"
                }
                DRG.update(drg)  # Append the dictionary to the list
        return DRG

    def get_pr1(self, message_type):
        PR1 = []
        for app in self.app_app_ids:
            for patient in app.patient_visit_ids:

                for ps_info in app.procedures_segment_ids:
                    pr1 = {
                        "PR1": {
                            "procedureCode": app.service_type_id.code if app.service_type_id.code else '',
                            "procedureDescription": app.service_type_id.name,
                            "procedureDateTime": app.start_date.strftime(
                                '%Y%m%d%H%M%S') if app.start_date else None,
                        }
                        # 'SetIDPR1': ps_info.set_id_prl,
                        # "ProcedureCode": {
                        #     "Identifier": app.service_type_id.code if app.service_type_id.code else '',
                        #     "Text": app.service_type_id.name
                        # },
                        # 'ProcedureDescription': app.service_type_id.name,
                        # 'ProcedureDateTime': app.start_date.strftime(
                        #     '%Y%m%d%H%M%S') if app.start_date else None,
                        # 'Surgeon': {
                        #     "IdNumber": str(app.sheryan_id) if app.sheryan_id else '',
                        #     "FamilyName": patient.last_name if patient.last_name else '',
                        #     "GivenName": patient.first_name if patient.first_name else ''
                        # },
                        # 'ProcedurePriority': "1",
                    }
                    PR1.append(pr1)
        return PR1

    def get_pr1_a04(self, message_type,appointment):
        PR1 = []
        for app in appointment:
            # for patient in app.patient_visit_ids:
            for ps_info in app.procedures_segment_ids:
                pr1 = {
                    # "code": "17110^Laser Hair Reduction^C4",
                    # "description": "Laser Hair Reduction",
                    # "dateTime": "20241125173000",
                    # "attendingDoctor":  ps_info.surgeon if ps_info.surgeon else '',
                    # "operator": "SHERYAN"
                    "code": str(
                        ps_info.procedure_code) if ps_info.procedure_code else '' + '^' + ps_info.procedure_id.name if ps_info.procedure_id.name else '' + '^' + app.service_type_id.code if app.service_type_id.code else '',
                    "description": ps_info.procedure_id.name if ps_info.procedure_id.name else '',
                    'codingSystem': 'C4',
                    "dateTime": app.start_date.strftime(
                        '%Y%m%d%H%M%S') if app.start_date else None,

                    "attendingDoctor": '',
                    "operator": "SHERYAN"

                }
                PR1.append(pr1)
        return PR1

    def get_gt1(self, message_type):
        GT1 = {}
        for guarantor in self.guarantor_ids:
            gt1 = {
                # "guarantorID": guarantor.set_id_gtl,
                # "guarantorName": {
                #     "firstName": guarantor.first_name if guarantor.first_name else '',
                #     "lastName": guarantor.last_name if guarantor.last_name else '',
                # },
                # "guarantorAddress": {
                #     "streetAddress": guarantor.street if guarantor.street else '',
                #     "city": guarantor.city if guarantor.city else '',
                #     "state": guarantor.states.name if guarantor.states.name else '',
                #     "zip": guarantor.zip if guarantor.zip else '',
                # },
                # "guarantorPhoneNumber": guarantor.phone_number if guarantor.phone_number else ''
                # # 'SetIDGT1': guarantor.set_id_gtl,
                # # 'GuarantorName': guarantor.guarantor_name,
                "guarantorName": guarantor.full_name,
                "guarantorRelationship": guarantor.guarantor_relationship.name,
                "guarantorAddress": guarantor.complete_address,
                "guarantorPhoneNumber": guarantor.phone_number if guarantor.phone_number else ''
            }

            GT1.update(gt1)

            if not GT1:
                GT1 = [{}]
        return GT1

    def get_gt1_a04(self, message_type):
        GT1 = {}
        for guarantor in self.guarantor_ids:
            gt1 = {
                "id": guarantor.set_id_gtl,
                "name": guarantor.full_name if guarantor.full_name else '',
                "address": guarantor.complete_address,
                "phone": guarantor.phone_number if guarantor.phone_number else ''

                # 'SetIDGT1': guarantor.set_id_gtl,
                # 'GuarantorName': guarantor.guarantor_name,
            }

            GT1.update(gt1)

            if not GT1:
                GT1 = [{}]
        return GT1

    def get_in1_o01(self, message_type):
        IN1 = {}
        for ins in self.insurance_ids:
            in1 = {

                "insurancePlanID": ins.health_plan_id,
                "insuranceCompanyName": ins.in_company_name,
                "insurancePolicyNumber": ins.policy_no,
                "insuredPhoneNumber": self.mobile,
                "insuredName": ins.insured_name

            }
            IN1.update(in1)
        return IN1

    def get_in1(self, message_type):
        IN1 = {}
        for ins in self.insurance_ids:
            in1 = {
                "IN1": {
                    "insurancePlanID": ins.health_plan_id,
                    "insuranceCompanyName": ins.in_company_name,
                    "insurancePolicyNumber": ins.policy_no,
                    "insuredParty": {
                        "insuredName": {
                            "firstName": self.first_name,
                            "lastName": self.last_name
                        },
                        "relationshipToPatient": "Self",
                        "insuredDateOfBirth": self.dob.strftime('%Y%m%d')
                    },
                    "insuredPhoneNumber": self.mobile
                }
                # 'SetIDIN1': ins.set_id_inr,
                # "HealthPlanID": {
                #     "Identifier": ins.health_plan_id,
                #     "Text": ins.company_des
                # },
                # "InsuranceCompanyID": {
                #     "IdNumber": ins.insurence_compny_id,
                #     "AssigningAuthority": ins.company_des
                # },
                # "InsuranceCompanyName": {
                #     "OrganizationName": ins.in_company_name,
                #     "AssigningAuthority": ins.company_des
                # },
                # 'PolicyNumber': ins.policy_no,

            }
            IN1.update(in1)
        return IN1

    def get_in1_a04(self, message_type):
        IN1 = {}
        for ins in self.insurance_ids:
            in1 = {
                "planID": ins.health_plan_id,
                "companyName": ins.in_company_name,
                "policyNumber": ins.policy_no,
                "coverageType": "Full",
                "effectiveDate": ins.effective_date.strftime('%Y%m%d') if ins.effective_date else None,
                "expirationDate": ins.effective_date.strftime('%Y%m%d') if ins.effective_date else None,
                "subscriber": {
                    "lastName": self.last_name,
                    "firstName": self.first_name
                },
                "subscriberRelationship": "Self",
                "subscriberDOB": self.dob.strftime('%Y%m%d'),
                "subscriberID": ins.health_plan_id
            }

            # 'SetIDIN1': ins.set_id_inr,
            # "HealthPlanID": {
            #     "Identifier": ins.health_plan_id,
            #     "Text": ins.company_des
            # },
            # "InsuranceCompanyID": {
            #     "IdNumber": ins.insurence_compny_id,
            #     "AssigningAuthority": ins.company_des
            # },
            # "InsuranceCompanyName": {
            #     "OrganizationName": ins.in_company_name,
            #     "AssigningAuthority": ins.company_des
            # },
            # 'PolicyNumber': ins.policy_no,

            IN1.update(in1)
        return IN1

    def get_zsc(self, message_type):
        ZSC = {}
        for zsc in self.z_consent_ids:
            zsc = {
                "optOutFlag": str(self.is_facility),
                "optOutFlagDate": self.date_message.strftime('%Y%m%d%H%M%S') if self.date_message else None,
                "vipIndicator": str(self.is_vip),
                "vipIndicatorDate": self.event_date.strftime('%Y%m%d%H%M%S') if self.event_date else None,

                # "Facility": {
                #     "IsOpted": str(self.is_facility),
                #     "FromDate": self.date_message.strftime('%Y%m%d%H%M%S') if self.date_message else None,
                #     "LastUpdatedDate": self.date_message.strftime('%Y%m%d%H%M%S') if self.date_message else None
                # },
                # "Global": {
                #     "IsOpted": str(self.is_global),
                #     "FromDate": zsc.global_from_date.strftime('%Y%m%d%H%M%S') if zsc.global_from_date else None,
                #     "LastUpdatedDate": zsc.global_from_date.strftime('%Y%m%d%H%M%S') if zsc.global_from_date else None
                # },
                # "VIP": {
                #     "IsVIP": str(self.is_vip),
                #     "FromDate": self.event_date.strftime('%Y%m%d%H%M%S') if self.event_date else None,
                #     "LastUpdatedDate": self.event_date.strftime('%Y%m%d%H%M%S') if self.event_date else None
                # }

            }
            ZSC.update(zsc)
        return ZSC

    def get_zsh(self, message_type):
        ZSH = []
        for social_history in self.segment_social_history_ids:
            # for fly_history in self.segment_family_history_ids:
            zsh = {
                "habit": social_history.social_habits.name,
                "quantity": social_history.social_habit_qty_id.name,
                "category": social_history.social_habit_categorys.name,
            }
            ZSH.append(zsh)
        if not ZSH:
            ZSH = [{}]
        return ZSH

    def get_zfh(self, message_type):
        ZFH = []

        # for app in self.app_app_ids:
        for parties in self.associated_parties_ids:
            # for fh in app.diagnosis_information_ids:
            for family_history in self.segment_family_history_ids:
                zfh = {

                    "condition": family_history.status,
                    "relation": parties.relationship.name,
                }
                ZFH.append(zfh)

        if not ZFH:
            ZFH = [{}]

        return ZFH

    def get_orc_vo4(self, message_type,appointment):
        ORC = {}

        for app in appointment:
            for common in app.common_order_ids:
                orc = {
                    "orderControl": common.order_control.code,
                    "orderNumber": common.name + '^' + 'Lesprit Medical Clinic LLC',
                    "orderStatus": "CM",
                    "timestamp": common.date_transaction.strftime('%Y%m%d%H%M%S'),
                    "operator": {
                        "status": "CM^^HIV(+) patient",
                        "codeSystem": common.confidentiality_code.name,
                        "medication": common.order_type.code
                    },

                }

                ORC.update(orc)

        return ORC

    def get_orc_ro1(self, message_type, appointment):
        ORC = {}

        for app in appointment:
            for common in app.common_order_ids:
                orc = {
                    "orderControl": common.order_control.code,
                    "orderNumber": "170" + '^' + 'TESTHOS20',
                    "orderStatus": common.order_status.code,
                    "timestamp": common.date_transaction.strftime('%Y%m%d%H%M%S') if common.date_transaction else None,
                    "operator": {
                        "status": common.confidentiality_code.code +'^' +'^'+"NAB019",
                        "codeSystem": common.confidentiality_code.code,
                        "medication": common.order_type.code
                    },

                }

                ORC.update(orc)
        if not ORC:
            ORC = {
                "orderControl": "OK",
                "orderNumber": "23^^Lesprit Medical Clinic LLC",
                "orderControlIP": "IP",
                "orderStatus": "U^^NAB019",
                "orderType": "MED",
                "timestamp": "",
                "operator": {
                    "status": "CM^^HIV(+) patient",
                    "codeSystem": "",
                    "medication": ""
                }
            }

        return ORC

    def get_orc(self, message_type,appointment):
        ORC = {}

        for app in appointment:
            for common in app.common_order_ids:
                orc = {
                    "orderNumber": common.name + '^' + 'Lesprit Medical Clinic LLC',
                    "orderControl": common.order_control.code,
                    "orderControlIP": "IP",
                    "orderStatus": common.confidentiality_code.code +'^' +'^'+"NAB019",
                    "orderType": common.order_type.code,

                    # 'OrderControl': common.order_control.code,
                    # 'PlacerOrderNumber': common.name,
                    # 'OrderStatus': common.order_status.code,
                    # "QuantityTiming": {
                    #     "Quantity": common.quantity,
                    #     "Interval": common.interval,
                    #     "Duration": common.duration,
                    #     "Priority": common.priority,
                    #     "Text": common.text
                    # },
                    # 'DateTimeTransaction': common.date_transaction.strftime('%Y%m%d%H%M%S'),
                    # "OrderingProvider": {
                    #     "IdNumber": common.ordering_provider,
                    #     "FamilyName": common.family_name,
                    #     "GivenName": common.given_name
                    # },
                    # "ConfidentialityCode": {
                    #     "Identifier": common.confidentiality_code.code,
                    #     "Text": common.confidentiality_code.name,
                    #     "NameOfCodingSytem": common.confidentiality_code.code
                    # },
                    # "OrderType": "MED"
                }

                ORC.update(orc)

        return ORC

    def get_orc_o01(self, message_type,appointment):
        ORC = {}

        for app in appointment:
            for common in app.common_order_ids:
                orc = {

                    "orderControl": common.order_control.code,
                    "orderNumber": common.name + '^' + 'Lesprit Medical Clinic LLC',
                    "placerOrderNumber": common.name,
                    "fillerOrderNumber": common.name,
                    "orderStatus": common.order_status.code,
                    "timestamp": common.date_transaction.strftime('%Y%m%d%H%M%S'),
                    "orderedBy": "",
                    "operator": {
                        "status": common.order_status.code,
                        "codeSystem": common.confidentiality_code.name,
                        "medication": common.order_type.code
                    }

                    # 'OrderControl': common.order_control.code,
                    # 'PlacerOrderNumber': common.name,
                    # 'OrderStatus': common.order_status.code,
                    # # "QuantityTiming": {
                    # #     "Quantity": common.quantity,
                    # #     "Interval": common.interval,
                    # #     "Duration": common.duration,
                    # #     "Priority": common.priority,
                    # #     "Text": common.text
                    # # },
                    # 'DateTimeTransaction': common.date_transaction.strftime('%Y%m%d%H%M%S'),
                    # "OrderingProvider": {
                    #     "IdNumber": common.ordering_provider,
                    #     "FamilyName": common.family_name,
                    #     "GivenName": common.given_name
                    # },
                    # "ConfidentialityCode": {
                    #     "Identifier": common.confidentiality_code.code,
                    #     "Text": common.confidentiality_code.name,
                    #     "NameOfCodingSytem": common.confidentiality_code.code
                    # },
                    # "OrderType": "MED"
                }

                ORC.update(orc)

        return ORC

    def get_obr(self, message_type):
        OBR = {}

        for app in self.app_app_ids:
            for obr in app.observations_result_ids:
                obr = {
                    "PlacerOrderNumber": obr.placer_order_number,
                    "FillerOrderNumber": obr.placer_order_number,
                    "UniversalServiceIdentifier": {
                        "Identifier": obr.universal_service_code,
                        "Text": obr.universal_service_des,
                        "NameOfCodingSytem": "C4"
                    },
                    "ObservationDateTime": obr.observation_date_time.strftime('%Y%m%d%H%M%S'),
                    "OrderingProvider": {
                        "IdNumber": "12536648",
                        "FamilyName": obr.first_name,
                        "GivenName": obr.last_name
                    },
                    "ResultsReportDate": obr.results_report_date.strftime('%Y%m%d%H%M%S'),
                    "DiagnosticServiceSectionID": obr.diagnostic_service_section_id.code,
                    "ResultStatus": obr.result_status_id.code
                }

                OBR.update(obr)

        return OBR

    def get_obr_ro1(self, message_type):
        OBR = {}

        for app in self.app_app_ids:
            for obr in app.observations_result_ids:
                obr = {

                    "setID": obr.placer_order_number,
                    "universalServiceIdentifier": obr.diagnostic_service_section_id.name,
                    "priority": obr.priority,
                    "observationDateTime": obr.observation_date_time.strftime('%Y%m%d%H%M%S'),
                    "resultsReportDateTime": obr.results_report_date.strftime('%Y%m%d%H%M%S'),
                    "orderingProvider": obr.full_name,
                    "resultCopiesTo": obr.mail_id,
                    #
                    # "OrderControl": obr.order_control_id.code,
                    # "PlacerOrderNumber": obr.placer_order_number,
                    # "OrderStatus": obr.order_status_id.code,
                    # "DateTimeTransaction": obr.observation_date_time.strftime('%Y%m%d%H%M%S'),
                    # "OrderingProvider": {
                    #     "IdNumber": "12536648",
                    #     "FamilyName": obr.first_name,
                    #     "GivenName": obr.last_name
                    # },
                    # "ConfidentialityCode": {
                    #     "Identifier": obr.confidentiality_id.code,
                    #     "Text": obr.confidentiality_id.name,
                    #     "NameOfCodingSytem": obr.confidentiality_id.name
                    # },
                    # "OrderType": obr.order_type_id.code
                }

                OBR.update(obr)

        return OBR

    def get_rxo(self, message_type,appointment):
        RXO = {}

        for app in appointment:
            for pharmacy in app.pharmacy_order_ids:
                rxo = {

                    "medicationCode": (
                                          str(pharmacy.requested_give_code) if pharmacy.requested_give_code else ''
                                      ) + '^' +
                                      (
                                          str(pharmacy.requested_give_name) if pharmacy.requested_give_name else ''
                                      ) + '^' +
                                      (str("DDC")),
                    "dosage": pharmacy.dosage,
                    "unitOfMeasurement": pharmacy.requested_given_unit,
                    "administrationRoute": pharmacy.providers_administration_instructions.name,
                    "administrationTime": pharmacy.administratio_time.strftime(
                        '%Y%m%d') if pharmacy.administratio_time else None,
                    "expirationDate": pharmacy.expiration_date.strftime('%Y%m%d') if pharmacy.expiration_date else None,
                    "status": pharmacy.status,
                    "additionalInfo": "20201021133709"

                    # "RequestedGiveCode": {
                    #     "Identifier": pharmacy.requested_give_code,
                    #     "Text": pharmacy.requested_give_name,
                    #     "NameOfCodingSytem": "DDC"
                    # },
                    # "RequestedGiveAmountMinimum": pharmacy.requested_amount_minimum,
                    # "RequestedGiveUnits": {
                    #     "Identifier": pharmacy.requested_amount_minimum,
                    #     "Text": pharmacy.requested_given_unit,
                    #     "NameOfCodingSytem": "DDC"
                    # },
                    # "RequestedDosageForm": {
                    #     "Identifier": pharmacy.requested_amount_minimum,
                    #     "Text": pharmacy.requested_given_unit
                    # },
                    # "ProvidersAdministrationInstructions": {
                    #     "Identifier": pharmacy.providers_administration_instructions.code,
                    #     "Text": pharmacy.providers_administration_instructions.name,
                    #     "NameOfCodingSytem": pharmacy.providers_administration_instructions.code
                    # }
                }

                RXO.update(rxo)

        return RXO

    def get_rxo_o01(self, message_type,appointment):
        RXO = {}
        for app in self.app_app_ids:
            for pharmacy in app.pharmacy_order_ids:
                rxo = {
                    "medicationId": pharmacy.requested_give_code,
                    "medicationName": pharmacy.requested_give_name,
                    "dosage": pharmacy.requested_amount_minimum,
                    "unitOfMeasure": pharmacy.requested_given_unit,
                    "dosageUnit": pharmacy.requested_given_unit,
                    "routeOfAdministration": pharmacy.providers_administration_instructions.name,
                    "quantity": pharmacy.frequency

                    # "RequestedGiveCode": {
                    #     "Identifier": pharmacy.requested_give_code,
                    #     "Text": pharmacy.requested_give_name,
                    #     "NameOfCodingSytem": "DDC"
                    # },
                    # "RequestedGiveAmountMinimum": pharmacy.requested_amount_minimum,
                    # "RequestedGiveUnits": {
                    #     "Identifier": pharmacy.requested_amount_minimum,
                    #     "Text": pharmacy.requested_given_unit,
                    #     "NameOfCodingSytem": "DDC"
                    # },
                    # "RequestedDosageForm": {
                    #     "Identifier": pharmacy.requested_amount_minimum,
                    #     "Text": pharmacy.requested_given_unit
                    # },
                    # "ProvidersAdministrationInstructions": {
                    #     "Identifier": pharmacy.providers_administration_instructions.code,
                    #     "Text": pharmacy.providers_administration_instructions.name,
                    #     "NameOfCodingSytem": pharmacy.providers_administration_instructions.code
                    # }
                }

                RXO.update(rxo)

        return RXO

    def get_prb(self, message_type,appointment):
        PRB = {}

        for app in appointment:
            for problem in app.problems_form_ids:
                prb = {
                    "LastModifiedDate": problem.action_date_time.strftime(
                        '%Y%m%d%H%M%S') if problem.action_date_time else None,
                    "ProblemCode": problem.problem_id_code,
                    "ProblemDescription": problem.problem_des_id.name,
                    "ICDCode":  'I10',
                    "ProblemStatus": problem.status_id.name if problem.status_id else '',
                    "OnsetDate": problem.Problem_onset_date.strftime('%Y%m%d') if problem.Problem_onset_date else None,
                    "ResolvedDate": problem.Problem_life_cycle_date.strftime(
                        '%Y%m%d') if problem.Problem_life_cycle_date else None,
                    "FinalDiagnosisStatus": "F",
                    "LocalCode": "LOCALCODE",
                    "SNOMEDCode": problem.life_cycle_status_id.code

                }

                PRB.update(prb)
        return PRB

    def get_nte(self, message_type):
        NTE = []

        for app in self.app_app_ids:
            for nte in app.nte_ids:
                nte = {
                    'SetIDZFH': nte.set_id_nte,
                }
                NTE.append(nte)

        if not NTE:
            NTE = [{}]
        return NTE

    def get_nte_r01(self, message_type,appointment):
        NTE = []

        for app in appointment:
            for nte in app.nte_ids:
                nte = {
                    "noteType": nte.source_comment,
                    "noteText": nte.note,
                }
                NTE.append(nte)

        if not NTE:
            NTE = [{}]
        return NTE

    def get_nte_t02(self, message_type,appointment):
        NTE = []

        for app in appointment:
            for nte in app.nte_ids:
                nte = {
                    # "setId": nte.set_id_nte,
                    "sourceOfComment": nte.source_comment,
                    "comment": nte.note,
                }
                NTE.append(nte)

        if not NTE:
            NTE = [{}]
        return NTE

    def get_txa(self, message_type,appointment):
        TXA = {}

        for app in appointment:
            for tx in app.transcription_document_ids:
                for observation in app.observations_ids:
                    txa = {

                        "reportDate": tx.activity_date_time.strftime('%Y%m%d%H%M%S'),
                        "operator": "90002225^P^Test^One^^^^^TESTHOS20^^^^PROVID",
                        "documentNumber": datetime.now().strftime('%Y%m%d%H%M%S'),
                        "documentFileName": observation.pdf_filename,
                        "uniqueDocumentNumber":tx.unique_file_number,
                        "completionStatus": tx.document_completion_status_id.code,
                        "availabilityStatus":tx.document_availability_status_id.code,
                        "transcriptionist": "90002225^P^Test^One^^^^^TESTHOS20^^^^PROVID",
                        #
                        # "documentType": txa.documents_type.name,
                        # "documentContent": txa.unique_document_number,
                        # "completionStatus": txa.document_completion_status_id.code,

                        #
                        # 'SetIDTXA': txa.name,
                        # "DocumentType": txa.documents_type.code,
                        # "ActivityDateTime": txa.activity_date_time.strftime('%Y%m%d%H%M%S'),
                        # "PrimaryActivityProviderCodeName": {
                        #     "IdNumber": txa.activity_provider_code,
                        #     "FamilyName": txa.first_name,
                        #     "GivenName": txa.last_name
                        # },
                        # "TranscriptionDateTime": txa.transcription_date_time.strftime('%Y%m%d%H%M%S'),
                        # "OriginatorCodeName": txa.originator_code_name,
                        # "UniqueDocumentNumber": txa.unique_document_number,
                        # 'UniqueDocumentFileName': txa.unique_file_number,
                        # 'DocumentCompletionStatus': txa.document_completion_status_id.code,
                        # "DocumentAvailabilityStatus": txa.document_availability_status_id.code

                    }

                TXA.update(txa)
        return TXA

    def get_mrg(self, message_type):
        MGR = {}
        first_app = self.app_app_ids.browse(self.ids)
        if first_app:
            mgr = {
                "previousPatientID": self.id,
                "previousPatientIdentifierList": [
                    "987654321"
                ],
                "previousPatientName": {
                    "firstName": self.first_name,
                    "lastName": self.last_name
                }
                # 'PriorPatientIdentifierList': self.id,
                # 'PriorVisitNumber': first_app.name,
            }
            MGR.update(mgr)

        return MGR

    def get_mrg_a04(self, message_type):
        MGR = {}
        first_app = self.app_app_ids.browse(self.ids)
        if first_app:
            mgr = {
                "mrn": "10046",
                "assigningAuthority": "TESTHOS20"
            }
            MGR.update(mgr)

        return MGR

    def get_values_a04(self, message_type):
        demo_list = []

        MSH = self.get_msh(message_type)
        EVN = self.get_evn(message_type)
        PID = self.get_pid_a04(message_type)
        MRG = self.get_mrg_a04(message_type)

        demo_list.append({"messageHeader": MSH})
        demo_list.append({"event": EVN})
        demo_list.append({"patient": PID})
        demo_list.append({"merge": MRG})

        merged_dict = {}
        for entry in demo_list:
            merged_dict.update(entry)

        return {'value': merged_dict, 'student': self.id}

    def action_register_a28(self, ):
        if not self.is_vip_sent:
            if self.is_vip:
                self.is_vip_sent = True

            values = self.get_values_a04('A28')
            message = self.env['message.type'].search([('message_type', '=', 'A28')])
            if message:
                login_url = message.link
            else:
                raise ValidationError("A28 Message type not found ,Please Configure before sending request !")

            headers_1 = {
                "Content-Type": "application/json",
            }
            body = values
            a28_response = requests.post(login_url, data=json.dumps(body), headers=headers_1)
            status_code = a28_response.status_code
            if status_code == 200:
                a28_result = json.loads(a28_response.text)
                message.action_send(a28_result['Details'], values['value'], student=self.id)
                self.message_post(body="Register request send to NABIDH")
            else:
                raise ValidationError("Request failed : %s" % a28_response.text)

    # def action_register(self, message_type,):
    #     if not self.is_vip_sent:
    #         if self.is_vip:
    #             self.is_vip_sent = True
    #         values = self.get_values_a04(message_type)
    #         message = self.env['message.type'].search([('message_type', '=', message_type)])
    #         self.message_type = message.name
    #         if message:
    #             login_url = message.link
    #
    #         else:
    #             raise ValidationError("A04 Message type not found ,Please Configure before sending request !")
    #
    #         headers_1 = {
    #             "Content-Type": "application/json",
    #         }
    #         body = values['value']
    #         a04_response = requests.post(login_url, data=json.dumps(body), headers=headers_1)
    #         print(a04_response,"a04_response")
    #         status_code = a04_response.status_code
    #
    #         if a04_response:
    #             a04_result = json.loads(a04_response.text)
    #             message.action_send(a04_result['Details'], values['value'], a04_result['HL7Message'], values['student'])
    #             self.message_post(body="Checkin request send to NABIDH")
    #         else:
    #             raise ValidationError("Request failed : %s" % a04_response.text)

    def action_register(self, message_type,):
        if not self.is_vip_sent:
            if self.is_vip:
                self.is_vip_sent = True
            values = self.get_values_a04(message_type)
            message = self.env['message.type'].search([('message_type', '=', message_type)])
            self.message_type = message.name
            if message:
                login_url = message.link
                # login_url = 'https://developerstg.dha.gov.ae/api/nabidhtesting/hl7testutility?app_id=a830a5be&app_key=10ea058592008b19969f3116832962b8'
            else:
                raise ValidationError("A04 Message type not found ,Please Configure before sending request !")

            headers_1 = {
                "Content-Type": "application/json",
            }
            body = values['value']
            a04_response = requests.post(login_url, data=json.dumps(body), headers=headers_1)
            status_code = a04_response.status_code

            if a04_response.status_code == 200:
                a04_result = json.loads(a04_response.text)
                message.action_hl7_url(a04_result.get('HL7Message'))
                print(message.nabidh_status,"iiiiiiiiiiii")
                message.action_send(
                    a04_result.get('Details'),
                    values['value'],
                    a04_result.get('HL7Message'),
                    values['student'],status =message.nabidh_status
                )
                self.message_post(body=f"A04(Checkin) request sent to NABIDH. Status: {message.nabidh_status}")
                return message.nabidh_status

            else:
                raise ValidationError(f"Request failed with status {a04_response.status_code}: {a04_response.text}")

    def get_values_A03(self, message_type,appointment):
        demo_list = []
        MSH = self.get_msh(message_type)
        EVN = self.get_evn(message_type)
        PID = self.get_pid_a03(message_type)
        PV1 = self.get_pv1_ao3(message_type,appointment)
        PV2 = self.get_vl_a03(message_type,appointment)
        AL1 = self.get_al1(message_type,appointment)
        ZSH = self.get_zsh(message_type)

        demo_list.append({"messageHeader": MSH})
        demo_list.append({"event": EVN})
        demo_list.append({"patient": PID})
        demo_list.append({"visit": PV1})
        demo_list.append({"vitalSigns": PV2})
        demo_list.append({"allergies": AL1})
        demo_list.append({"socialHistory": ZSH})
        merged_dict = {}
        for entry in demo_list:
            merged_dict.update(entry)

        return {'value': merged_dict, 'student': self.id}

    def discharge_event(self,message_type,appointment):
        if not self.is_vip_sent:
            if self.is_vip:
                self.is_vip_sent = True
            values = self.get_values_A03(message_type,appointment)
            message = self.env['message.type'].search([('message_type', '=', message_type)])
            self.message_type = message.name
            if message:
                login_url = message.link
            else:
                raise ValidationError("A03 Message type not found ,Please Configure before sending request !")
            headers_1 = {
                "Content-Type": "application/json",
            }
            body = values['value']
            a03_response = requests.post(login_url, data=json.dumps(body), headers=headers_1)
            if a03_response:
                a03_result = json.loads(a03_response.text)
                message.action_hl7_url(a03_result['HL7Message'])
                message.action_send(a03_result['Details'], values['value'], a03_result['HL7Message'], values['student'],status=message.nabidh_status)
                self.message_post(body=f"A03(Discharge)  sent to NABIDH. Status: {message.nabidh_status}")
                return message.nabidh_status
            else:
                raise ValidationError("Request failed : %s" % a03_response.text)


    def cancel_admit(self, message_type,appointment):
        if not self.is_vip_sent:
            if self.is_vip:
                self.is_vip_sent = True
            values = self.get_values_A11(message_type,appointment)
            message = self.env['message.type'].search([('message_type', '=', message_type)])
            self.message_type = message.name
            if message:

                login_url = message.link
            else:
                raise ValidationError("A11 Message type not found ,Please Configure before sending request !")

            headers_1 = {
                "Content-Type": "application/json",
            }
            body = values['value']
            a11_response = requests.post(login_url, data=json.dumps(body), headers=headers_1)
            if a11_response:
                # if 'message' not in a11_response or not a11_response['message']:
                #     raise ValidationError(
                #         "The 'message' field is missing or empty in the response, but the status code is {}.".format(
                #             a11_response.status_code))

                a11_result = json.loads(a11_response.text)
                message.action_hl7_url(a11_result['HL7Message'])
                message.action_send(a11_result['Details'], values['value'], a11_result['HL7Message'], values['student'],status=message.nabidh_status)
                self.message_post(body=f"A11(Cancellation)  sent to NABIDH.\n "
                                       f"Status: {message.nabidh_status}")
                return message.nabidh_status
            else:
                raise ValidationError("Request failed : %s" % a11_response.text)

    def get_values_A08(self, message_type,appointment):
        demo_list = []
        MSH = self.get_msh(message_type)
        EVN = self.get_evn_a08(message_type)
        PID = self.get_pid_a31(message_type)
        PV1 = self.get_pv1_A31(message_type,appointment)
        OBX = self.get_obx_a04(message_type,appointment)
        AL1 = self.get_al1_a04(message_type,appointment)
        PR1 = self.get_pr1_a04(message_type,appointment)
        ZSH = self.get_zsh(message_type)

        demo_list.append({"messageHeader": MSH})
        demo_list.append({"event": EVN})
        demo_list.append({"patient": PID})
        demo_list.append({"visit": PV1})
        demo_list.append({"observations": OBX})
        demo_list.append({"allergies": AL1})
        demo_list.append({"procedures": PR1})
        demo_list.append({"socialHistory": ZSH})
        merged_dict = {}
        for entry in demo_list:
            merged_dict.update(entry)

        return {'value': merged_dict, 'student': self.id}

    def action_update(self,message_type,appointment):
        print(appointment,"appointmentddddddddd")
        if not self.is_vip_sent:
            if self.is_vip:
                self.is_vip_sent = True
            values = self.get_values_A08('A08',appointment)
            message = self.env['message.type'].search([('message_type', '=', 'A08')])
            self.message_type = message.name
            if message:
                login_url = message.link
            else:
                raise ValidationError("A08 Message type not found ,Please Configure before sending request !")
            headers_1 = {
                "Content-Type": "application/json",
            }
            body = values['value']
            a31_response = requests.post(login_url, data=json.dumps(body), headers=headers_1)
            if a31_response:
                a31_result = json.loads(a31_response.text)
                message.action_hl7_url(a31_result['HL7Message'])
                message.action_send(a31_result['Details'], values['value'], a31_result['HL7Message'], values['student'],status=message.nabidh_status)
                self.message_post(body=f"A08(Update) sent to NABIDH. Status: {message.nabidh_status}")
                return message.nabidh_status
            else:
                raise ValidationError("Request failed : %s" % a31_response.text)

    def get_values_A31(self, message_type,appointment):
        demo_list = []
        MSH = self.get_msh(message_type)
        EVN = self.get_evn(message_type)
        PID = self.get_pid_a03(message_type)
        PV1 = self.get_pv1_ao3(message_type,appointment)
        PV2 = self.get_vl_a03(message_type,appointment)
        AL1 = self.get_al1(message_type,appointment)

        ZSH = self.get_zsh(message_type)

        demo_list.append({"messageHeader": MSH})
        demo_list.append({"event": EVN})
        demo_list.append({"patient": PID})
        demo_list.append({"visit": PV1})
        demo_list.append({"vitalSigns": PV2})
        demo_list.append({"allergies": AL1})

        demo_list.append({"socialHistory": ZSH})
        merged_dict = {}
        for entry in demo_list:
            merged_dict.update(entry)

        return {'value': merged_dict, 'student': self.id}

    def get_values_A11(self, message_type,appointment):
        demo_list = []
        MSH = self.get_msh(message_type)
        EVN = self.get_evn(message_type)
        PID = self.get_pid_a03(message_type)
        PV1 = self.get_pv1_ao3(message_type,appointment)
        PV2 = self.get_vl_a03(message_type,appointment)
        AL1 = self.get_al1(message_type,appointment)
        ZSH = self.get_zsh(message_type)

        demo_list.append({"messageHeader": MSH})
        demo_list.append({"event": EVN})
        demo_list.append({"patient": PID})
        demo_list.append({"visit": PV1})
        demo_list.append({"vitalSigns": PV2})
        demo_list.append({"allergies": AL1})

        demo_list.append({"socialHistory": ZSH})
        merged_dict = {}
        for entry in demo_list:
            merged_dict.update(entry)

        return {'value': merged_dict, 'student': self.id}

    def action_update_a31(self):

        if not self.is_vip_sent:
            if self.is_vip:
                self.is_vip_sent = True
            values = self.get_values_A31('A31')
            message = self.env['message.type'].search([('message_type', '=', 'A31')])
            self.message_type = message.name
            if message:
                login_url = message.link
            else:
                raise ValidationError("A31 Message type not found ,Please Configure before sending request !")
            headers_1 = {
                "Content-Type": "application/json",
            }
            body = values
            a31_response = requests.post(login_url, data=json.dumps(body), headers=headers_1)
            if a31_response:
                a31_result = json.loads(a31_response.text)
                message.action_send(a31_result['Details'], values['value'], a31_result['HL7Message'], values['student'])
                self.message_post(body="Update request send to NABIDH")
            else:
                raise ValidationError("Request failed : %s" % a31_response.text)

    def get_msh_A39(self, message_type):
        return {
            "sendingApplication": "odoo",
            "receivingApplication": "NABIDH",
            "messageType": "ADT^A39",
            "messageControlID": self.date_message.strftime('%Y%m%d%H%M%S') if self.date_message else None,
            "timestamp": self.date_message.strftime('%Y%m%d%H%M%S') if self.date_message else None,
            "encodingCharacters": "^~&",
            "version": "2.5",
            "characterSet": "UTF-8"
        }

    def get_evn_A39(self, message_type):
        return {
            "eventTypeCode":  dict(self._fields['message_type']._description_selection(self.env)).get(message_type, '').split('^')[-1].strip(),
            "recordedDateTime": self.event_date.strftime('%Y%m%d%H%M%S') if self.event_date else None,
            "operator": {
                "id": "SHERYAN^7333258",
                "name": "SHERYAN"
            },
            "timestamp": self.event_date.strftime('%Y%m%d%H%M%S') if self.event_date else None,
        }

    def get_evn_T02(self, message_type):
        return {

            "type":
                dict(self._fields['message_type']._description_selection(self.env)).get(message_type, '').split('^')[
                    -1].strip(),
            "timestamp": self.event_date.strftime('%Y%m%d%H%M%S') if self.event_date else None,
            "operator": {
                "id": "SHERYAN^7333258",
                "name": "SHERYAN"
            }
            # "eventTypeCode":  dict(self._fields['message_type']._description_selection(self.env)).get(message_type, '').split('^')[-1].strip(),
            # "recordedDateTime": self.event_date.strftime('%Y%m%d%H%M%S') if self.event_date else None,
            # "operator": {
            #     "id": "SHERYAN^7333258",
            #     "name": "SHERYAN"
            # },
            # "timestamp": self.event_date.strftime('%Y%m%d%H%M%S') if self.event_date else None,
        }
    def get_pid_a39(self, message_type):
        PID = {}

        for pat_iden in self.patient_identifer_ids:
            # for parties in self.associated_parties_ids:
            pid = {
                "mrn": pat_iden.patient_identifier_list,
                "assigningAuthority": "TESTHOS20",
                "lastName": str(self.last_name) if self.last_name else '',
                "firstName": str(self.first_name) if self.first_name else '',
                "middleName": str(self.middle_name) if self.middle_name else '',
                # "gender": self.gender,
                "gender": next(iter(dict(self._fields['gender']._description_selection(self.env)).values()))[:1].upper(),
                "dob": self.dob.strftime('%Y%m%d'),
                "address": {
                    "city": str(self.city) if self.city else '',
                    "state": str(self.state_id.name) if self.state_id.name else '',
                    "zip": str(self.zip) if self.zip else '',
                    # "country": str(parties.country.code) if parties.country.code else '',
                },
                "phoneNumber": {
                    "home": self.mobile
                },
                "maritalStatus": pat_iden.marital_status.code,
                "religion": pat_iden.religion.code,
                "nationality": pat_iden.nationality.code,
                "language": pat_iden.primary_lang.code,

                "updatedTimestamp": datetime.now().strftime('%Y%m%d%H%M%S') ,
            }
            PID.update(pid)

        return PID

    def get_values_A39(self, message_type):
        demo_list = []
        nabidh_type = "ADT^A39"
        msgUid = "45320688191"
        sendingFacility = "TESTHOS20/TCODE10"
        MSH = self.get_msh_A39(message_type)
        EVN = self.get_evn_A39(message_type)
        PID = self.get_pid_a39(message_type)
        MRG = self.get_mrg_a04(message_type)

        demo_list.append({"nabidh_type": nabidh_type})
        demo_list.append({"msgUid": msgUid})
        demo_list.append({"sendingFacility": sendingFacility})
        demo_list.append({"MSH": MSH})
        demo_list.append({"EVN": EVN})
        demo_list.append({"PID": PID})
        demo_list.append({"MRG": MRG})

        merged_dict = {}
        for entry in demo_list:
            merged_dict.update(entry)
        return {'value': merged_dict, 'student': self.id}

    def merge_patient(self):
        if not self.is_vip_sent:
            if self.is_vip:
                self.is_vip_sent = True
            values = self.get_values_A39('A39')
            message = self.env['message.type'].search([('message_type', '=', 'A39')])
            self.message_type = message.name
            if message:
                login_url = message.link
            else:
                raise ValidationError("A39 Message type not found ,Please Configure before sending request !")
            headers_1 = {
                "Content-Type": "application/json",
            }
            body = values['value']
            a39_response = requests.post(login_url, data=json.dumps(body), headers=headers_1)
            if a39_response:
                a39_result = json.loads(a39_response.text)
                message.action_hl7_url(a39_result['HL7Message'])
                message.action_send(a39_result['Details'], values['value'], a39_result['HL7Message'], values['student'],status=message.nabidh_status)
                self.message_post(body=f"A39(Merge) request sent to NABIDH. Status: {message.nabidh_status}")
            else:
                raise ValidationError("Request failed : %s" % a39_response.text)

    def action_merge_patient(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'base.partner.merge.automatic.wizard',
            'view_mode': 'form',
            'target': 'new',
            'name': 'Merge Patient',
            'context': {'default_patient_id': self.id }
        }

    def get_values_v04(self, message_type,appointment):
        demo_list = []
        MSH = self.get_msh(message_type)
        EVN = self.get_evn(message_type)
        PID = self.get_pid_vo4(message_type)
        PV1 = self.get_pv1_ao3(message_type,appointment)
        ORC = self.get_orc(message_type,appointment)
        RXO = self.get_rxo(message_type,appointment)

        demo_list.append({"messageHeader": MSH})
        demo_list.append({"event": EVN})
        demo_list.append({"patient": PID})
        demo_list.append({"visit": PV1})
        demo_list.append({"order": ORC})
        demo_list.append({"medication": RXO})
        merged_dict = {}
        for entry in demo_list:
            merged_dict.update(entry)

        return {'value': merged_dict, 'student': self.id}

    def action_vo4(self,message_type,appointment):
        if not self.is_vip_sent:
            if self.is_vip:
                self.is_vip_sent = True

            values = self.get_values_v04('V04',appointment)

            message = self.env['message.type'].search([('message_type', '=', 'V04')])
            self.message_type = message.name
            if message:

                login_url = message.link
            else:
                raise ValidationError("V04 Message type not found,Please Configure before sending request!")

            headers_1 = {
                "Content-Type": "application/json",
            }
            body = values['value']

            vo4_response = requests.post(login_url, data=json.dumps(body), headers=headers_1)

            if vo4_response:
                vo4_result = json.loads(vo4_response.text)
                message.action_hl7_url(vo4_result['HL7Message'])
                message.action_send(vo4_result['Details'], values['value'], vo4_result['HL7Message'], values['student'],status=message.nabidh_status)
                # self.message_post(body="V04 request send to NABIDH")
                self.message_post(body=f"V04(Vaccination message) sent to NABIDH. Status: {message.nabidh_status}")
                return message.nabidh_status

            else:
                raise ValidationError("Request failed : %s" % vo4_response.text)

    def get_values_r01(self, message_type,appointment):
        demo_list = []

        MSH = self.get_msh(message_type)
        EVN = self.get_evn(message_type)
        PID = self.get_pid_vo4(message_type,)
        PV1 = self.get_pv1_ao3(message_type,appointment)
        ORC = self.get_orc_ro1(message_type,appointment)
        OBX = self.get_obx(message_type,appointment)
        SPM = self.get_spm_r01(message_type,appointment)
        NTE = self.get_nte_r01(message_type,appointment)


        demo_list.append({"messageHeader": MSH})
        demo_list.append({"event": EVN})
        demo_list.append({"patient": PID})
        demo_list.append({"visit": PV1})
        demo_list.append({"order": ORC})
        demo_list.append({"observations": OBX})
        demo_list.append({"specimen": SPM})
        demo_list.append({"Note": NTE})

        merged_dict = {}
        for entry in demo_list:
            merged_dict.update(entry)

        return {'value': merged_dict, 'student': self.id}

    def unsolicited_transmission_observation(self,message_type,appointment):
        if not self.is_vip_sent:
            if self.is_vip:
                self.is_vip_sent = True

            values = self.get_values_r01('R01',appointment)

            message = self.env['message.type'].search([('message_type', '=', 'R01')])
            self.message_type = message.name
            if message:

                login_url = message.link
            else:
                raise ValidationError("R01 Message type not found ,Please Configure before sending request !")

            headers_1 = {
                "Content-Type": "application/json",
            }
            body = values['value']

            r01_response = requests.post(login_url, data=json.dumps(body), headers=headers_1)

            if r01_response:
                r01_result = json.loads(r01_response.text)
                message.action_hl7_url(r01_result['HL7Message'])
                print( message.action_hl7_url(r01_result['HL7Message'])," message.action_hl7_url(r01_result['HL7Message'])")
                message.action_send(r01_result['Details'], values['value'], r01_result['HL7Message'], values['student'],status=message.nabidh_status)
                # self.message_post(body="R01 request send to NABIDH")
                self.message_post(body=f"R01(Observation) sent to NABIDH. Status: {message.nabidh_status}")
                return message.nabidh_status

            else:
                raise ValidationError("Request failed : %s" % r01_response.text)

    def get_values_O01(self, message_type,appointment):
        demo_list = []

        MSH = self.get_msh(message_type)
        EVN = self.get_evn(message_type)
        PID = self.get_pid_oo1(message_type)
        PV1 = self.get_pv1_o01(message_type,appointment)
        vitalSigns = self.get_vl_a03(message_type,appointment)
        allergies = self.get_al1(message_type,appointment)
        socialHistory = self.get_zsh(message_type)

        demo_list.append({"messageHeader": MSH})
        demo_list.append({"event": EVN})
        demo_list.append({"patient": PID})
        demo_list.append({"visit": PV1})
        demo_list.append({"vitalSigns": vitalSigns})
        demo_list.append({"allergies": allergies})
        demo_list.append({"socialHistory": socialHistory})

        merged_dict = {}
        for entry in demo_list:
            merged_dict.update(entry)

        return {'value': merged_dict, 'student': self.id}

    def oder_message_O01(self,message_type,appointment):
        if not self.is_vip_sent:
            if self.is_vip:
                self.is_vip_sent = True

            values = self.get_values_O01(message_type,appointment)
            message = self.env['message.type'].search([('message_type', '=', 'O01')])
            self.message_type = message.name
            if message:

                login_url = message.link
            else:
                raise ValidationError("O01 Message type not found ,Please Configure before sending request !")

            headers_1 = {
                "Content-Type": "application/json",
            }
            body = values['value']

            o01_response = requests.post(login_url, data=json.dumps(body), headers=headers_1)
            if o01_response:
                o01_result = json.loads(o01_response.text)
                message.action_hl7_url(o01_result['HL7Message'])
                message.action_send(o01_result['Details'], values['value'], o01_result['HL7Message'], values['student'],status=message.nabidh_status)
                self.message_post(body="O01(Order Message) sent to NABIDH. Status: {message.nabidh_status}")
                return message.nabidh_status
            else:
                raise ValidationError("Request failed : %s" % o01_response.text)

    def get_values_pc1(self, message_type,appointment):

        demo_list = []
        nabidh_type = "PPR^PC1"
        msgUid = "uuid"
        sendingFacility = "TESTHOS20/TCODE10"
        MSH = self.get_msh(message_type)
        EVN = self.get_evn(message_type)
        PID = self.get_pid_pc1(message_type)
        PV1 = self.get_pv1_r01(message_type,appointment)
        PRB = self.get_prb(message_type,appointment)

        demo_list.append({"nabidh_type": nabidh_type})
        demo_list.append({"msgUid": msgUid})
        demo_list.append({"sendingFacility": sendingFacility})
        demo_list.append({"messageHeader": MSH})
        demo_list.append({"event": EVN})
        demo_list.append({"patient": PID})
        demo_list.append({"visit": PV1})
        demo_list.append({"PRB": PRB})
        # demo_list.append({"NTE": NTE})
        # demo_list.append({"NK1": NK1})
        # demo_list.append({"PV1": PV1})
        # demo_list.append({"PV2": PV2})
        # demo_list.append({"DG1": DG1})

        # demo_list.append({"ORC": ORC})
        # demo_list.append({"OBR": OBR})

        merged_dict = {}
        for entry in demo_list:
            merged_dict.update(entry)
        return {'value': merged_dict, 'student': self.id}

    def problem_record_pc1(self,message_type,appointment):
        if not self.is_vip_sent:
            if self.is_vip:
                self.is_vip_sent = True

            values = self.get_values_pc1(message_type,appointment)
            message = self.env['message.type'].search([('message_type', '=', message_type)])
            self.message_type = message.name
            if message:
                login_url = message.link
            else:
                raise ValidationError("PC1 Message type not found ,Please Configure before sending request !")

            headers_1 = {
                "Content-Type": "application/json",
            }
            body = values['value']
            pc1_response = requests.post(login_url, data=json.dumps(body), headers=headers_1)
            if pc1_response:
                pc1_result = json.loads(pc1_response.text)
                message.action_hl7_url(pc1_result['HL7Message'])
                message.action_send(pc1_result['Details'], values['value'], pc1_result['HL7Message'], values['student'],status=message.nabidh_status)
                self.message_post(body=f"PC1(Problem Record message) sent to NABIDH. Status: {message.nabidh_status}")
                return message.nabidh_status
            else:
                raise ValidationError("Request failed : %s" % pc1_response.text)

    def get_values_t02(self, message_type,appointment):
        demo_list = []
        MSH = self.get_msh(message_type)
        EVN = self.get_evn_T02(message_type)
        PID = self.get_pid_t02(message_type,appointment)
        PV1 = self.get_pv1_t02(message_type,appointment)
        TXA = self.get_txa(message_type,appointment)
        OBX = self.get_obx_t02(message_type,appointment)
        NTE = self.get_nte_t02(message_type,appointment)
        # ZSC = self.get_zsc(message_type)

        demo_list.append({"messageHeader": MSH})
        demo_list.append({"event": EVN})
        demo_list.append({"patient": PID})
        demo_list.append({"visit": PV1})
        demo_list.append({"transcription": TXA})
        demo_list.append({"observations": OBX})
        demo_list.append({"notes": NTE})
        # demo_list.append({"ZSC": ZSC})

        merged_dict = {}
        for entry in demo_list:
            merged_dict.update(entry)

        return {'value': merged_dict,'student': self.id}

    def original_document_notification(self,message_type,appointment):
        if not self.is_vip_sent:
            if self.is_vip:
                self.is_vip_sent = True

            values = self.get_values_t02(message_type,appointment)
            message = self.env['message.type'].search([('message_type', '=', 'T02')])
            if message:

                login_url = message.link
            else:
                raise ValidationError("T02 Message type not found ,Please Configure before sending request !")

            headers_1 = {
                "Content-Type": "application/json",
            }
            body = values['value']
            t02_response = requests.post(login_url, data=json.dumps(body), headers=headers_1)
            if t02_response:
                t02_result = json.loads(t02_response.text)
                message.action_hl7_url(t02_result['HL7Message'])
                message.action_send(t02_result['Details'], values['value'], t02_result['HL7Message'], values['student'],
                                    status=message.nabidh_status)
                self.message_post(body=f"T02 sent to NABIDH. Status: {message.nabidh_status}")
                return message.nabidh_status
            else:
                raise ValidationError("Request failed : %s" % t02_response.text)

    # def original_document_notification(self):
    #     if not self.is_vip_sent:
    #         if self.is_vip:
    #             self.is_vip_sent = True
    #
    #         message = self.env['message.type'].search([('message_type', '=', 'T02')])
    #         self.message_type = message.name
    #         if message:
    #             login_url = message.link
    #         else:
    #             raise ValidationError("T02 Message type not found, Please Configure before sending request!")
    #
    #         headers_1 = {
    #             "Content-Type": "text/plain",
    #         }
    #         body = ''
    #         MSH = self.get_msh(message)
    #         PID = self.get_pid_t02(message)
    #         PV1 = self.get_pv1_t02(message)
    #         TXA = self.get_txa(message)
    #         OBX = self.get_obx_t02(message)
    #         NTE = self.get_nte_t02(message)
    #
    #         MSH_segment = f"MSH|^~\\&|{MSH.get('sendingApplication', '')}|DEPT|CLINIC|{MSH.get('timestamp', '')}|| ADT ^ A01 ||" \
    #                       f"{MSH.get('messageControlID', '')}|P|2.3"
    #
    #         pid_segment = (f"PID|{PID.get('patientId', '')}||123456^^^HOSPITAL||"
    #                        f"{PID.get('name', {}).get('firstName', '')}^"
    #                        f"{PID.get('name', {}).get('GivenName', '')}^"
    #                        f"{PID.get('name', {}).get('lastName', '')}||"
    #                        f"{PID.get('dateOfBirth', '')}|{PID.get('gender', '')}|||"
    #                        f"{PID.get('address', {}).get('streetAddress', '')}^^"
    #                        f"{PID.get('address', {}).get('city', '')}^CA^"
    #                        f"{PID.get('address', {}).get('zip', '')}^"
    #                        f"{PID.get('address', {}).get('state', '')}||"
    #                        f"{PID.get('phoneNumber', '')}||(555)555-5678||S|123456789")
    #
    #         PV1_segment = f"PV1|{PV1.get('patientID', '')}|{PV1.get('patientClass', '')}|200^301^01||||" \
    #                       f"{PV1.get('attendingDoctor', {}).get('id', '')}^" \
    #                       f"{PV1.get('attendingDoctor', {}).get('name', {}).get('firstName', '')}^" \
    #                       f"{PV1.get('attendingDoctor', {}).get('name', {}).get('middleName', '')}^" \
    #                       f"{PV1.get('attendingDoctor', {}).get('name', {}).get('firstName', '')}|India"
    #
    #         TXA_segment = f"TXA|{TXA.get('documentType', '')}|{TXA.get('documentContent', '')}|{TXA.get('completionStatus', '')}"
    #         obx_segment = ""
    #         if OBX:
    #             obx_segment = f"OBX|{OBX[0].get('observationId', '')}|{OBX[0].get('valueType', '')}|" \
    #                           f"{OBX[0].get('observationId', '')}|{OBX[0].get('units', '')}"
    #         nte_segment = ""
    #         if NTE:
    #             nte_segment = f"NTE|{NTE[0].get('setId', '')}|{NTE[0].get('sourceOfComment', '')}|" \
    #                           f"{NTE[0].get('comment', '')}"
    #         data = f"{MSH_segment} \n{pid_segment} \n{PV1_segment} \n{TXA_segment} \n{obx_segment} \n{nte_segment}"
    #
    #         t02_response = requests.post(login_url, data=data, headers=headers_1)
    #         if t02_response:
    #             t02_result = json.loads(t02_response.text)
    #             print(t02_result,"t02_result")
    #             message.action_hl7_url(t02_result['HL7Message'])
    #             message.action_send(t02_result['Details'], t02_result['HL7Message'], self.id,
    #                                 status=message.nabidh_status)
    #             # message.action_send(t02_result['Details'], t02_result['HL7Message'], self.id)
    #             self.message_post(body="T02 request sent to NABIDH")
    #         else:
    #             raise ValidationError("Request failed: %s" % t02_response.text)

    def edit_notification(self,message_type,appointment):
        if not self.is_vip_sent:
            if self.is_vip:
                self.is_vip_sent = True

            values = self.get_values_t02(message_type,appointment)
            message = self.env['message.type'].search([('message_type', '=', 'T08')])
            if message:

                login_url = message.link
            else:
                raise ValidationError("T08 Message type not found ,Please Configure before sending request !")

            headers_1 = {
                "Content-Type": "text/plain",
            }
            body = ''
            MSH = self.get_msh(message)
            PID = self.get_pid_t02(message,appointment)
            PV1 = self.get_pv1_t02(message,appointment)
            TXA = self.get_txa(message,appointment)
            OBX = self.get_obx_t02(message,appointment)
            NTE = self.get_nte_t02(message,appointment)
            # 'MSH|^~\&|HOSPITAL|DEPT|CLINIC|202312181200||ADT^A01|MSG123456|P|2.3
            MSH_segment = f"MSH|^~\&|{MSH.get('sendingApplication', '')}|DEPT|CLINIC|{MSH.get('timestamp', '')}|| ADT ^ A01 |MSG123456|P|2.3"

            pid_segment = (
                f"PID|1"  # Set ID (PID-1)
                f"||{PID.get('mrn', '')}^^^{PID.get('assigningAuthority', 'HOSPITAL')}||"  # PID-3: Patient ID List
                f"{PID.get('lastName', '')}^{PID.get('firstName', '')}^{PID.get('middleName', '')}||"  # PID-5: Patient Name
                f"{PID.get('dob', '')}|{PID.get('gender', '')}|||"  # PID-7 & PID-8
                f"{PID.get('address', {}).get('streetAddress', '')}^^"
                f"{PID.get('address', {}).get('city', '')}^{PID.get('address', {}).get('state', '')}^"
                f"{PID.get('address', {}).get('zip', '')}^USA||"  # PID-11: Address
                f"{PID.get('phoneNumber', {}).get('home', '')}||"  # PID-13: Home Phone
                f"{PID.get('phoneNumber', {}).get('business', '')}||"  # PID-14: Business Phone
                f"{PID.get('maritalStatus', '')}|"  # PID-16: Marital Status
                f"{PID.get('religion', '')}|"  # PID-17: Religion
                f"{PID.get('secondaryMrn', '')}|"  # PID-18: Secondary Identifier
                f"{PID.get('emiratesId', '')}"  # PID-19: National ID
            )

            # f"{PID.get('phoneNumber', '')}||(555)555-5678||S|123456789")

            # PV1_segment = f"PV1|{PV1.get('patientID', '')}|{PV1.get('patientClass', '')}|200^301^01||||" \
            #               f"{PV1.get('attendingDoctor', {}).get('id', '')}^" \
            #               f"{PV1.get('attendingDoctor', {}).get('name', {}).get('firstName', '')}^" \
            #               f"{PV1.get('attendingDoctor', {}).get('name', {}).get('middleName', '')}^" \
            #               f"{PV1.get('attendingDoctor', {}).get('name', {}).get('firstName', '')}|India"

            PV1_segment = (
                f"PV1|1|{PV1.get('visitType', '')}|200^301^01||||"
                f"{PV1.get('attendingDoctor', {}).get('id', '')}^"
                f"{PV1.get('attendingDoctor', {}).get('lastName', '')}^"
                f"{PV1.get('attendingDoctor', {}).get('firstName', '')}^"
                f"{PV1.get('attendingDoctor', {}).get('middleName', '')}|India"
                # f"{PV1.get('room', '')}^TESTHOS20^PLS|"
                # f"{PV1.get('admitDate', '')}|{PV1.get('visitStatus', '')}"
            )

            # TXA_segment = (
            #     f"TXA|1"  # Set ID
            #     f"|{TXA.get('activity_type', 'DISCHARGE SUMMARY')}"  # Document type
            #     f"|{TXA.get('document_completion_status_id', {}).get('code', 'FINAL')}"  # Completion status
            #     f"|{TXA.get('reportDate', '')}"  # Report Date/Time
            #     f"|{TXA.get('documentFileName', '')}"  # Document filename
            #     f"|{TXA.get('uniqueDocumentNumber', '')}"  # Unique Document Number
            #     f"|{TXA.get('document_completion_status_id', {}).get('code', '')}"  # Completion status code
            #     f"|{TXA.get('document_availability_status_id', {}).get('code', '')}"  # Availability status
            #     f"|{TXA.get('transcriptionist', '')}"  # Transcriptionist
            #     f"|{TXA.get('operator', '')}"
            # )
            TXA_segment = (
                f"TXA|1"  # Set ID
                f"|{TXA.get('activityType', 'DISCHARGE SUMMARY')}"  # Document type
                f"|{TXA.get('completionStatus', 'FINAL')}"  # Completion status
                f"|{TXA.get('reportDate', '')}"  # Report Date/Time
                f"|{TXA.get('documentFileName', '')}"  # Document filename
                f"|{TXA.get('uniqueDocumentNumber', '')}"  # Unique Document Number
                f"|{TXA.get('completionStatus', '')}"  # Completion status code (repeated)
                f"|{TXA.get('availabilityStatus', '')}"  # Availability status
                f"|{TXA.get('transcriptionist', '')}"  # Transcriptionist
                f"|{TXA.get('operator', '')}"  # Operator
            )

            # TXA_segment = f"TXA|{TXA.get('operator', '')}|{TXA.get('documentFileName', '')}|{TXA.get('completionStatus', '')}"
            obx_segment = ""
            if OBX:
                obx_segment = (
                    f"OBX|1"  # Set ID
                    f"|{OBX[0].get('valueType', '')}"  # Value Type (e.g., NM, TX)
                    f"|{OBX[0].get('observationId', '')}"  # Observation Identifier
                    f"|1"  # Observation Sub-ID
                    f"|{OBX[0].get('value', '')}"  # Observation Value
                    f"|{OBX[0].get('units', '')}"  # Units
                    f"|{OBX[0].get('abnormalFlags', '')}"  # Abnormal Flags
                    f"||||"  # Reference Range, Probability, Nature of Abnormal Test (optional)
                    f"{OBX[0].get('resultStatus', '')}"  # Result Status
                    f"|{OBX[0].get('timestamp', '')}"  # Observation Date/Time
                )

                # obx_segment = f"OBX|{OBX[0].get('observationId', '')}|{OBX[0].get('valueType', '')}|{OBX[0].get('abnormalFlags', '')}|" \
                #               f"{OBX[0].get('observationId', '')}|{OBX[0].get('units', '')}"
            nte_segment = ""
            if NTE:
                nte_segment = f"NTE|{NTE[0].get('setId', '')}|{NTE[0].get('sourceOfComment', '')}|" \
                              f"{NTE[0].get('comment', '')}"

            data = f"{MSH_segment} \n{pid_segment} \n{PV1_segment} \n{TXA_segment} \n{obx_segment} \n{nte_segment}"

            t08_response = requests.post(login_url, data=data, headers=headers_1)
            print(t08_response, "t08_result")
            if t08_response:
                t08_result = json.loads(t08_response.text)
                print(t08_result,"t08_result")
                message.action_hl7_url(t08_result['HL7Message'])
                message.action_send(t08_result['Details'], data, t08_result['HL7Message'], values['student'],
                                    status=t08_result['Status'])
                self.message_post(body=f"T08 sent to NABIDH. Status: {t08_result['Status']}")
                return t08_result['Status']
            else:
                raise ValidationError("Request failed: %s" % t08_response.text)

