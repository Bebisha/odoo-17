from odoo import models, fields, api, _
import random
import string

class KgPvAdditionalInfo(models.Model):
    _name = 'kg.pv.additional.info'

    _inherit = ['mail.thread', 'mail.activity.mixin']
    _mail_post_access = 'read'
    _description = 'Kg Patient Visit Additional Information'

    name = fields.Char(string='Name', copy=False, readonly=True, index=True, default=lambda self: _('New'))
    """mandatory fields"""

    admit_reason = fields.Char(string="Admit Reason")
    visit_description = fields.Char(string="Visit Description")

    """non mandatory fields"""

    prior_pending_loc=fields.Char(string="Prior Pending Location")
    accomodation_code=fields.Char(string="Accommodation Code")
    transfer_reason=fields.Char(string="Transfer Reason")
    patient_valuables=fields.Char(string="Patient Valuables")
    patient_valuables_loc=fields.Char(string="Patient Valuables Location")
    visit_user_code=fields.Char(string="Visit User Code")
    expected_admit_date=fields.Datetime(string="Expected Admit Date/Time")
    expected_discharg_date=fields.Datetime(string="Expected Discharge Date/Time")
    estimated_inpatient_stay=fields.Char(string="Estimated Length of Inpatient Stay")
    actual_inpatient_stay=fields.Char(string="Actual Length of Inpatient Stay")
    reff_source_code=fields.Char(string="Referral Source Code")
    prev_servc_date=fields.Date(string="Previous Service Date")
    employmnt_illness_indicator=fields.Char(string="Employment Illness Related Indicator")
    purge_status_code=fields.Char(string="Purge Status Code")
    purge_status_date=fields.Date(string="Purge Status Date")
    special_program_code=fields.Char(string="Special Program Code")
    retention_indicator=fields.Char(string="Retention Indicator")
    expected_no_insurence_plans=fields.Char(string="Expected Number of Insurance Plans")
    visit_publicity_code=fields.Char(string="Visit Publicity Code")
    visit_protection_indicator=fields.Char(string="Visit Protection Indicator")
    clinic_org_name=fields.Char(string="Clinic Organization Name")
    patient_status_code=fields.Char(string="Patient Status Code")
    visit_priority_code=fields.Char(string="Visit Priority Code")
    prev_treatment_date=fields.Date(string="Previous Treatment Date")
    expected_dischrg_dispostn=fields.Char(string="Expected Discharge Disposition")
    sign_file_date=fields.Date(string="Signature on File Date")
    first_similer_illness_date=fields.Date(string="First Similar Illness Date")
    patient_charg_adjustmnt_code=fields.Char(string="Patient Charge Adjustment Code")
    recurrng_servic_code=fields.Char(string="Recurring Service Code")
    billing_media_code=fields.Char(string="Billing Media Code")
    expected_surgry_date=fields.Datetime(string="Expected Surgery Date and Time")
    miltary_partnership_code=fields.Char(string="Military Partnership Code")
    miltary_non_avail_code=fields.Char(string="Military Non-Availability Code")
    newborn_baby_indicator=fields.Char(string="Newborn Baby Indicator")
    baby_detained_indicator=fields.Char(string="Baby Detained Indicator")
    mode_arrival_code=fields.Char(string="Mode of Arrival Code")
    recreational_drug_code=fields.Char(string="Recreational Drug Use Code")
    admission_level_care_code=fields.Char(string="Admission Level of Care Code")
    precaution_code=fields.Char(string="Precaution Code")
    patient_condition_code=fields.Char(string="Patient Condition Code")
    living_will_code=fields.Char(string="Living Will Code")
    organ_donar_code=fields.Char(string="Organ Donor Code")
    advance_dirctive_code=fields.Char(string="Advance Directive Code")
    patient_status_effective_code=fields.Date(string="Patient Status Effective Date")
    expected_loa_retrn_date=fields.Datetime(string="Expected LOA Return Date/Time")
    expected_pre_admisn_testng_date=fields.Datetime(string="Expected Pre-admission Testing Date/Time")
    notify_clergy_code=fields.Char(string="Notify Clergy Code")


    state = fields.Selection([('draft', 'Draft'),('submited','Submitted'),('cancel','Cancel')],string='Status', default='draft')


    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'): vals['name'] = self.env['ir.sequence'].next_by_code(
            'kg.pv.additional.info') or _('New')
        request = super(KgPvAdditionalInfo, self).create(vals)
        return request

    def btn_submit(self):
        self.write({'state': 'submited'})
        url = self.env['ir.config_parameter'].get_param('web.base.url')
        data = {
            'admit_reason' : self.admit_reason,
            'visit_description' : self.visit_description,
            'prior_pending_loc' : self.prior_pending_loc,
            'accomodation_code' : self.accomodation_code,
            'transfer_reason' : self.transfer_reason,
            'patient_valuables' : self.patient_valuables,
            'patient_valuables_loc' : self.patient_valuables_loc,
            'visit_user_code' : self.visit_user_code,
            # 'expected_admit_date' : self.expected_admit_date,
            # 'expected_discharg_date' : self.expected_discharg_date,
            'estimated_inpatient_stay' : self.estimated_inpatient_stay,
            'actual_inpatient_stay' : self.actual_inpatient_stay,
            'reff_source_code' : self.reff_source_code,
            # 'prev_servc_date' : self.prev_servc_date,
            'employmnt_illness_indicator' : self.employmnt_illness_indicator,
            'purge_status_code' : self.purge_status_code,
            # 'purge_status_date' : self.purge_status_date,
            'special_program_code' : self.special_program_code,
            'retention_indicator' : self.retention_indicator,
            'expected_no_insurence_plans' : self.expected_no_insurence_plans,
            'visit_publicity_code' : self.visit_publicity_code,
            'visit_protection_indicator' : self.visit_protection_indicator,
            'clinic_org_name' : self.clinic_org_name,
            'patient_status_code' : self.patient_status_code,
            'visit_priority_code' : self.visit_priority_code,
            # 'prev_treatment_date' : self.prev_treatment_date,
            'expected_dischrg_dispostn' : self.expected_dischrg_dispostn,
            # 'sign_file_date' : self.sign_file_date,
            # 'first_similer_illness_date' : self.first_similer_illness_date,
            'patient_charg_adjustmnt_code' : self.patient_charg_adjustmnt_code,
            'recurrng_servic_code' : self.recurrng_servic_code,
            'billing_media_code' : self.billing_media_code,
            # 'expected_surgry_date' : self.expected_surgry_date,
            'miltary_partnership_code' : self.miltary_partnership_code,
            'miltary_non_avail_code' : self.miltary_non_avail_code,
            'newborn_baby_indicator' : self.newborn_baby_indicator,
            'baby_detained_indicator' : self.baby_detained_indicator,
            'mode_arrival_code' : self.mode_arrival_code,
            'recreational_drug_code' : self.recreational_drug_code,
            'admission_level_care_code' : self.admission_level_care_code,
            'precaution_code' : self.precaution_code,
            'patient_condition_code' : self.patient_condition_code,
            'living_will_code' : self.living_will_code,
            'organ_donar_code' : self.organ_donar_code,
            'advance_dirctive_code' : self.advance_dirctive_code,
            'patient_status_effective_code' : self.patient_status_effective_code,
            # 'expected_loa_retrn_date' : self.expected_loa_retrn_date,
            # 'expected_pre_admisn_testng_date' : self.expected_pre_admisn_testng_date,
            'notify_clergy_code' : self.notify_clergy_code,
        }
        response_data = self.env['tdcc.api'].post(data, url)


    def btn_cancel(self):
        print("mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm")
        self.write({'state': 'cancel'})