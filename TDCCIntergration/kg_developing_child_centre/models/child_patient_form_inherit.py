from odoo import models, fields, api
import random
import string
import base64
from odoo import http, tools, _
from odoo.http import request

from odoo.tools import image_data_uri
from odoo.addons.base.models.ir_mail_server import extract_rfc2822_addresses


class partner(models.Model):
    _inherit = 'res.partner'

    set_id_pid = fields.Char(string='Set ID-PID')
    patient_id = fields.Char(string='Patient ID', required=False)
    patient_identifier_list = fields.Char(string='Patient Identifier List')
    alternt_patient_id_pid = fields.Char(string='Alternate Patient ID – PID ', required=False)
    middle_name = fields.Char(string='Middle Name ')
    mother_middle_name = fields.Char(string='Middle Name ')
    mother_last_name = fields.Char(string='Last Name ')
    gender = fields.Selection(selection_add=[('Unknown', 'Unknown')], string="Gender", )
    patient_alias = fields.Char(string='Patient Alias', )
    race = fields.Char(string='Race', )
    country_code = fields.Char(string='Country Code')
    phone_business = fields.Char(string="Phone Number - Business")
    primary_lang = fields.Many2one('res.lang', string="Primary Language")
    marital_status = fields.Selection([('Married', 'Married'),
                                       ('Unmarried', 'Unmarried')], string="Marital Status")
    religion = fields.Char(string="Religion", )


    patient_ssn_no = fields.Char(string="SSN Number – Patient", )

    patient_driver_licenc_no = fields.Char(string="Driver's License Number – Patient", required=False)
    mothers_identifier = fields.Char(string="Mother's Identifier", )
    ethnic_group = fields.Char(string="Ethnic Group", )
    birth_place = fields.Char(string="Birth Place", )
    # acc_number=fields.Char('Account Number', )
    multi_birth_indicator = fields.Selection([('Yes', 'Yes'),
                                              ('No', 'No')], string="Multiple Birth Indicator", )
    birth_order = fields.Char(string="Birth Order", )
    citizenship = fields.Char(string="Citizenship", )
    veterans_military_status = fields.Char(string="Veterans Military Status", required=False)
    patient_death_datetime = fields.Datetime('Patient Death Date and Time')
    patient_death_indicator = fields.Selection([('Yes', 'Yes'),
                                                ('No', 'No')], string="Patient Death Indicator", )
    identity_unknown_indicator = fields.Selection([('vip', 'V'), ('tourist', 'T'),
                                                   ('all dubai residents', 'O')], string="Identity Unknown Indicator",
                                                  help="V for VIP,T for Tourist and O for all residents in dubai ",
                                                  )
    identity_reliability_code = fields.Char(string="Identity Reliability Code", required=False)
    last_updated_datetime = fields.Datetime('Last Update Date/Time', )
    last_update_facility = fields.Char(string="Last Update Facility", )
    species_code = fields.Char(string="Species Code", required=False)
    breed_code = fields.Char(string="Breed Code", required=False)
    strain = fields.Char(string="Strain", required=False)
    production_class_code = fields.Char(string="Production Class Code", required=False)
    tribal_citizenship = fields.Char(string="Tribal Citizenship", required=False)

