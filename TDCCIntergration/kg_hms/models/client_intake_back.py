import requests
from odoo import models, fields, api, _


class ClientIntakeForm(models.Model):
    _name = 'client.intake.form'
    _description = 'Client Intake Form'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _default_terms_condition(self):
        res = self.env['ir.config_parameter'].sudo().get_param('client_intake_form_config.edit_and_create')
        self.edit_and_create = res

    edit_and_create = fields.Html(string='Bills of Rights/Privacy Information')

    name = fields.Char(string="Name", required=True, copy=False, default='New', readonly=True)
    first_name = fields.Char(string='First Name')
    last_name = fields.Char(string='Last Name')
    child_name = fields.Char(string='Full Name')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')])
    date_of_birth = fields.Date(string='Date of Birth')
    nationality = fields.Many2one('res.country', string='Nationality')
    primary_language = fields.Char(string='Primary Language')
    language_spoken = fields.Char(string='Language spoken at home')
    school_grade = fields.Char(string='School grade')
    contact_person = fields.Char(string='At School contact person')
    mother_name = fields.Char(string='Mother Name')
    phone_number_1 = fields.Char(string='Phone Number')
    occupation_1 = fields.Char(string='Occupation', tracking=True)
    mother_mail = fields.Char(string='Mother Email')
    father_name = fields.Char(string='Father Name')
    phone_number_2 = fields.Char(string='Phone Number')
    occupation_2 = fields.Char(string='Occupation')
    father_mail = fields.Char(string='Father Email')
    # company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    company_id = fields.Many2one('res.company')
    ref = fields.Char(string='Reference')

    parents_related_relative = fields.Selection([('yes', 'Yes'), ('no', 'No')],
                                                string='Are parents related / relatives?')
    center = fields.Char(string='Who referred you to our Centre')
    describe = fields.Text(string='Please describe your main concerns and what services are you looking for?')
    child_health = fields.Text(
        string='Has your child been assessed or evaluated by a health professional / therapist / educational psychologist')
    doc_front = fields.Binary(string='Front Side')
    doc_back = fields.Binary(string='Back Side')

    first_name_1 = fields.Char(string='First Name')
    last_name_1 = fields.Char(string='Last Name')
    first_name_2 = fields.Char(string='First Name')
    last_name_2 = fields.Char(string='Last Name')
    terms_condition = fields.Selection([('true', 'True'), ('false', 'False')],
                                       string='I have read, understood and agreed to the above Terms and Conditions. I understand that this document forms part of the requirements for beginning evaluation, therapy and / or support services with TDCC.')

    confirm = fields.Selection([('true', 'True'), ('false', 'False')],
                               string='I hereby confirm that the information provided herein is correct and complete and that the documents submitted along with this form are valid.')
    signature = fields.Binary(string='Signature')

    state = fields.Selection([('draft', 'Draft'), ('approve', 'Approved')], default='draft')
    is_submitted = fields.Boolean(string='Submit', default=False)
    partner_id = fields.Many2one('res.partner', string='Partner')

    _sql_constraints = [
        ('ref_unique', 'unique(ref)', 'This reference is already used!')
    ]


    def approve_action(self):
        self.state = 'approve'
        partner = self.env['res.partner'].create({
            'name': self.child_name,
            # 'first_name': self.first_name,
            # 'last_name': self.last_name,
            'phone': self.phone_number_1,
            'mobile': self.phone_number_2,
            # 'client_id': self.id,
            # 'dob': self.date_of_birth,
            # 'mother_name': self.mother_name,
            # 'gender': self.gender,
            'country_id': self.nationality.id,
            # 'primary_language': self.primary_language,
            # 'language_spoken': self.language_spoken,
            # 'school_grade': self.school_grade,
            # 'contact_person': self.contact_person,
        })
        self.partner_id = partner.id

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('client.intake.sequence')
        result = super(ClientIntakeForm, self).create(vals)
        # a = str(result.first_name) + ' ' + str(result.last_name)
        # result.child_name = a
        # x = ''.join(random.choices(string.ascii_lowercase, k=10))
        # result.ref = x
        # mail_template = self.env.ref('kg_developing_child_centre.client_mail_template')
        # mail_template.send_mail(result.id, force_send=True)
        return result





# class partner(models.Model):
#     _inherit = 'res.partner'
#
#     # gender = fields.Selection([('male', 'Male'), ('female', 'Female')])
#     date_of_birth = fields.Date(string='Date of Birth')
#     primary_language = fields.Char(string='Primary Language')
#     language_spoken = fields.Char(string='Language spoken at home')
#     school_grade = fields.Char(string='School grade')
#     contact_person = fields.Char(string='At School contact person')
#     client_id = fields.Many2one('client.intake.form', string='Client ID')
#     set_id_pid = fields.Char(string='Set ID-PID')
#     patient_id = fields.Char(string='Patient ID', required=False)
#     patient_identifier_list = fields.Char(string='Patient Identifier List')
#     alternt_patient_id_pid = fields.Char(string='Alternate Patient ID – PID ', required=False)
#     middle_name = fields.Char(string='Middle Name ')
#     mother_middle_name = fields.Char(string='Middle Name ')
#     mother_last_name = fields.Char(string='Last Name ')
#     gender = fields.Selection(selection_add=[('Unknown', 'Unknown')], string="Gender", )
#     patient_alias = fields.Char(string='Patient Alias', )
#     race = fields.Char(string='Race', )
#     country_code = fields.Char(string='Country Code')
#     phone_business = fields.Char(string="Phone Number - Business")
#     primary_lang = fields.Many2one('res.lang', string="Primary Language")
#     marital_status = fields.Selection([('Married', 'Married'),
#                                        ('Unmarried', 'Unmarried')], string="Marital Status")
#     religion = fields.Char(string="Religion", )
#     patient_ssn_no = fields.Char(string="SSN Number – Patient", )
#     patient_driver_licenc_no = fields.Char(string="Driver's License Number – Patient", required=False)
#     mothers_identifier = fields.Char(string="Mother's Identifier", )
#     ethnic_group = fields.Char(string="Ethnic Group", )
#     birth_place = fields.Char(string="Birth Place", )
#     # acc_number=fields.Char('Account Number', )
#     multi_birth_indicator = fields.Selection([('Yes', 'Yes'),
#                                               ('No', 'No')], string="Multiple Birth Indicator", )
#     birth_order = fields.Char(string="Birth Order", )
#     citizenship = fields.Char(string="Citizenship", )
#     veterans_military_status = fields.Char(string="Veterans Military Status", required=False)
#     patient_death_datetime = fields.Datetime('Patient Death Date and Time')
#     patient_death_indicator = fields.Selection([('Yes', 'Yes'),
#                                                 ('No', 'No')], string="Patient Death Indicator", )
#     identity_unknown_indicator = fields.Selection([('vip', 'V'), ('tourist', 'T'),
#                                                    ('all dubai residents', 'O')], string="Identity Unknown Indicator",
#                                                   help="V for VIP,T for Tourist and O for all residents in dubai ",
#                                                   )
#     identity_reliability_code = fields.Char(string="Identity Reliability Code", required=False)
#     last_updated_datetime = fields.Datetime('Last Update Date/Time', )
#     last_update_facility = fields.Char(string="Last Update Facility", )
#     species_code = fields.Char(string="Species Code", required=False)
#     breed_code = fields.Char(string="Breed Code", required=False)
#     strain = fields.Char(string="Strain", required=False)
#     production_class_code = fields.Char(string="Production Class Code", required=False)
#     tribal_citizenship = fields.Char(string="Tribal Citizenship", required=False)
#
#     mrm_sequence = fields.Char(string='MRM')
#
#     @api.model
#     def create(self, vals):
#         vals['mrm_sequence'] = self.env['ir.sequence'].next_by_code('res.partner')
#         result = super(partner, self).create(vals)
#         return result

    # def open_client_intake_form(self):
    #     ctx = {
    #         'default_name': self.client_id.name,
    #         'default_child_name': self.client_id.child_name,
    #         'default_first_name': self.client_id.first_name,
    #         'default_last_name': self.client_id.last_name,
    #         'default_gender': self.gender,
    #         'default_date_of_birth': self.dob,
    #         'default_nationality': self.country_id.id,
    #         'default_primary_language': self.primary_language,
    #         'default_language_spoken': self.language_spoken,
    #         'default_school_grade': self.school_grade,
    #         'default_contact_person': self.contact_person,
    #         'default_state': 'approve',
    #         'default_ref': self.ref
    #
    #     }
    #     return {
    #         'name': 'CI Form Details',
    #         'domain': [('partner_id', 'in', [self.id])],
    #         'context': ctx,
    #         'view_type': 'form',
    #         'view_mode': 'form',
    #         'target': 'new',
    #         'res_model': 'client.intake.form',
    #         'type': 'ir.actions.act_window'
    #     }
    #
    #
    # def pubish_action(self):
    #     url = self.env['ir.config_parameter'].get_param('web.base.url')
    #     data = {
    #         'set_id_pid' : self.set_id_pid,
    #         'patient_identifier_list' : self.patient_identifier_list,
    #         'patient_alias' : self.patient_alias,
    #         'race' : self.race,
    #         'phone_business' : self.phone_business,
    #         'primary_lang' : self.primary_lang.name,
    #         'marital_status' : self.marital_status,
    #         'religion' : self.religion,
    #         'patient_ssn_no': self.patient_ssn_no,
    #         'mothers_identifier' : self.mothers_identifier,
    #         'ethnic_group' : self.ethnic_group,
    #         'birth_place' : self.birth_place,
    #         'multi_birth_indicator' : self.multi_birth_indicator,
    #         'birth_order' : self.birth_order,
    #         'citizenship' : self.citizenship,
    #         'patient_death_datetime' : self.patient_death_datetime,
    #         'patient_death_indicator' : self.patient_death_indicator,
    #         'identity_unknown_indicator' : self.identity_unknown_indicator,
    #         'last_updated_datetime' : self.last_updated_datetime,
    #         'last_update_facility' : self.last_update_facility,
    #         'patient_id' : self.patient_id,
    #         'alternt_patient_id_pid' : self.alternt_patient_id_pid,
    #         'patient_driver_licenc_no' : self.patient_driver_licenc_no,
    #         'veterans_military_status' : self.veterans_military_status,
    #         'identity_reliability_code' : self.identity_reliability_code,
    #         'country_code' : self.country_code,
    #         'species_code' : self.species_code,
    #         'breed_code' : self.breed_code,
    #         'strain' : self.strain,
    #         'production_class_code' : self.production_class_code,
    #         'tribal_citizenship' : self.tribal_citizenship,
    #         'first_name' : self.first_name,
    #         'middle_name' : self.middle_name,
    #         'last_name' : self.last_name,
    #         'mother_name' : self.mother_name,
    #         'mother_middle_name' : self.mother_middle_name,
    #         'mother_last_name' : self.mother_last_name,
    #         'gender' : self.gender,
    #         'street': self.street,
    #         'street2': self.street2,
    #         'city_id' : self.city_id.name,
    #         'state_id' : self.state_id.name,
    #         'zip' : self.zip,
    #         'country_id' : self.country_id.name,
    #         'phone' : self.phone,
    #
    #     }
    #     response_data = self.env['tdcc.api'].post(data, url)



