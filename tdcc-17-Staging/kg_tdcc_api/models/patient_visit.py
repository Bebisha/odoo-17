from odoo import models, fields, api, _
import random
import string


class KgPatientVisit(models.Model):
    _name = 'kg.patient.visit'

    _inherit = ['mail.thread', 'mail.activity.mixin']
    _mail_post_access = 'read'
    _description = 'Kg Patient Visit'

    name = fields.Char(string='Name', copy=False, readonly=True, index=True, default=lambda self: _('New'))

    """mandatory fields"""

    set_id_pv1=fields.Char(string="Set ID – PV1")

    patient_class = fields.Selection([('I', 'I'), ('O', 'O'),('E','E')], default=None,
                                            string="Patient Class")
    assigned_patient_location = fields.Char(string="Assigned Patient Location")
    admission_type = fields.Selection([('A', 'A'), ('C', 'C'), ('E', 'E'),('L','L'),('N','N'),('R','R'),('U','U')], default=None,
                                     string="Admission Type")
    preadmit_number = fields.Char(string="Preadmit Number")
    attending_doctor = fields.Char(string="Attending Doctor")
    refering_doctor = fields.Char(string="Referring Doctor")
    consulting_doctor = fields.Char(string="Consulting Doctor")
    hospital_service = fields.Char(string="Hospital Service")
    admit_source = fields.Char(string="Admit Source")
    admitting_doctor = fields.Char(string="Admitting Doctor")
    visit_number = fields.Char(string="Visit Number")
    discharge_disposition = fields.Char(string="Discharge Disposition")
    discharge_location = fields.Char(string="Discharged to Location")
    admit_date_time = fields.Date(string="Admit Date/Time")
    discharg_date_time = fields.Date(string="Discharge Date/Time")

    """non mandatory fields"""

    prior_patient_location = fields.Char(string="Prior Patient Location")
    temporary_location = fields.Char(string="Temporary Location")
    preadmit_test_indicator = fields.Char(string="Preadmit Test Indicator")
    re_admission_indicator = fields.Char(string="Re-admission Indicator")
    ambulatory_service = fields.Char(string="Ambulatory Service")
    vip_indicator = fields.Char(string="VIP Indicator")
    patient_type = fields.Char(string="Patient Type")
    financial_class = fields.Char(string="Financial Class")
    charg_price_indicator = fields.Char(string="Charge Price Indicator")
    courtesy_code = fields.Char(string="Courtesy Code")
    credit_rating = fields.Char(string="Credit Rating")
    contract_code = fields.Char(string="Contract Code")
    contract_eff_date = fields.Date(string="Contract Effective Date")
    contract_amount = fields.Char(string="Contract Amount")
    contract_period = fields.Char(string="Contract Period")
    interest_code = fields.Char(string="Interest Code")
    transfer_bad_debt_code = fields.Char(string="Transfer to Bad Debt Code")
    transfer_bad_debt_date = fields.Date(string="Transfer to Bad Debt date")
    bad_debt_agency_code = fields.Char(string="Bad Debt Agency Code Not")
    bad_debt_transfer_amount = fields.Char(string="Bad Debt Transfer Amount")
    bad_debt_recovery_amount = fields.Char(string="Bad Debt Recovery Amount")
    delete_account_indicator = fields.Char(string="Delete Account Indicator")
    delete_account_date = fields.Date(string="Delete Account Date")
    diet_type = fields.Char(string="Diet Type")
    servicing_facility = fields.Char(string="Servicing Facility")
    bed_status = fields.Char(string="Bed Status")
    account_status = fields.Char(string="Account Status")
    pending_location = fields.Char(string="Pending Location")
    prior_temp_location = fields.Char(string="Prior Temporary Location")
    current_patient_balance = fields.Char(string="Current Patient Balance")
    total_charges = fields.Char(string="Total Charges")
    total_adjustments = fields.Char(string="Total Adjustments")
    total_payments = fields.Char(string="Total Payments")
    alternative_visit_id= fields.Char(string="Alternate Visit ID")
    visit_indicator= fields.Char(string="Visit Indicator")
    other_helthcr_provider= fields.Char(string="Other Healthcare Provider")

    state = fields.Selection([('draft', 'Draft'),('submited','Submitted'),('cancel','Cancel')],string='Status', default='draft')


    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'): vals['name'] = self.env['ir.sequence'].next_by_code(
            'kg.patient.visit') or _('New')
        request = super(KgPatientVisit, self).create(vals)
        return request

    def btn_submit(self):
        self.write({'state': 'submited'})
        url = self.env['ir.config_parameter'].get_param('web.base.url')
        data = {
            'set_id_pv1' : self.set_id_pv1,
            'patient_class' : self.patient_class,
            'assigned_patient_location' : self.assigned_patient_location,
            'admission_type' : self.admission_type,
            'preadmit_number' : self.preadmit_number,
            'attending_doctor' : self.attending_doctor,
            'refering_doctor' : self.refering_doctor,
            'consulting_doctor' : self.consulting_doctor,
            'hospital_service' : self.hospital_service,
            'admit_source' : self.admit_source,
            'admitting_doctor' : self.admitting_doctor,
            'visit_number' : self.visit_number,
            'discharge_disposition' : self.discharge_disposition,
            'discharge_location' : self.discharge_location,
            # 'admit_date_time' : self.admit_date_time,
            # 'discharg_date_time' : self.discharg_date_time,
            'prior_patient_location' : self.prior_patient_location,
            'temporary_location' : self.temporary_location,
            'preadmit_test_indicator' : self.preadmit_test_indicator,
            're_admission_indicator' : self.re_admission_indicator,
            'ambulatory_service' : self.ambulatory_service,
            'vip_indicator' : self.vip_indicator,
            'patient_type' : self.patient_type,
            'financial_class' : self.financial_class,
            'charg_price_indicator' : self.charg_price_indicator,
            'courtesy_code' : self.courtesy_code,
            'credit_rating' : self.credit_rating,
            'contract_code' : self.contract_code,
            # 'contract_eff_date' : self.contract_eff_date,
            'contract_eff_date' : self.contract_eff_date,
            'contract_amount' : self.contract_amount,
            'contract_period' : self.contract_period,
            'interest_code' : self.interest_code,
            'transfer_bad_debt_code' : self.transfer_bad_debt_code,
            # 'transfer_bad_debt_date' : self.transfer_bad_debt_date,
            'bad_debt_agency_code' : self.bad_debt_agency_code,
            'bad_debt_transfer_amount' : self.bad_debt_transfer_amount,
            'bad_debt_recovery_amount' : self.bad_debt_recovery_amount,
            'delete_account_indicator' : self.delete_account_indicator,
            # 'delete_account_date' : self.delete_account_date,
            'diet_type' : self.diet_type,
            'servicing_facility' : self.servicing_facility,
            'bed_status' : self.bed_status,
            'account_status' : self.account_status,
            'pending_location' : self.pending_location,
            'prior_temp_location' : self.prior_temp_location,
            'current_patient_balance' : self.current_patient_balance,
            'total_charges' : self.total_charges,
            'total_adjustments' : self.total_adjustments,
            'total_payments' : self.total_payments,
            'alternative_visit_id' : self.alternative_visit_id,
            'visit_indicator' : self.visit_indicator,
            'other_helthcr_provider' : self.other_helthcr_provider,

        }
        response_data = self.env['tdcc.api'].post(data, url)

    def btn_cancel(self):
        print("mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm")
        self.write({'state': 'cancel'})