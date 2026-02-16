from odoo import models, fields, api, _
import random
import string


class KgGurantorSegment(models.Model):
    _name = 'kg.guarantor.segment'

    _inherit = ['mail.thread', 'mail.activity.mixin']
    _mail_post_access = 'read'
    _description = 'Kg Procedures Segment'

    name = fields.Char(string='Name', copy=False, readonly=True, index=True, default=lambda self: _('New'))
    """mandatory fields"""

    set_id_gt1 = fields.Char(string="Set ID – GT1")
    gurantor_number = fields.Char(string="Guarantor Number")
    gurantor_name = fields.Char(string="Guarantor Name")
    gurantor_type = fields.Char(string="Guarantor Type", help="Example--- Employer, Self, Family, Friend, etc.")
    gurantor_relationship = fields.Char(string="Guarantor Relationship", help="Example--- Brother,Mother,Father etc.")
    gurantor_ssn = fields.Char(string="Guarantor SSN", help="15 digits Emirates Id in this field")
    gurantor_emplyr_name = fields.Char(string="Guarantor Employer Name",
                                       help="The name of the guarantor's employer, if the employer is a persond")
    gurantor_emp_status = fields.Char(string="Guarantor Employment Status", help="Guarantor Employment Status Code")
    gurantor_addres = fields.Text(string="Guarantor Address")
    gurantor_employer_addres = fields.Text(string="Guarantor Employer Address")
    gurantor_phnno_hom = fields.Integer(string="Guarantor Phone Number – Home")
    gurantor_phnno_business = fields.Integer(string="Guarantor Phone Number – Business")
    gurantor_employer_phnno = fields.Integer(string="Guarantor Employer Phone Number")
    gurantor_dob = fields.Date(string="Guarantor Date/Time Of Birth")
    gurantor_start_date = fields.Date(string="Guarantor Date – Begin")
    gurantor_end_date = fields.Date(string="Guarantor Date – End")
    guarantor_administrative_sex = fields.Selection([('male', 'Male'), ('female', 'Female'), ('unknown', 'Unknown')],
                                                    default=None, string="Guarantor Administrative Sex")
    gurantor_emp_id_no = fields.Char(string="Guarantor Employer ID Number")
    job_title = fields.Char(string="Job Title", help="The guarantor's job title")
    job_code = fields.Char(string="Job Code/Class", help="The guarantor's occupation")
    emp_orgnz_name = fields.Char(string="Guarantor Employer's Organization Name",
                                 help="The name of the guarantor's employer, if the employer is an organization")
    gurantor_hire_eff_date = fields.Date(string="Guarantor Hire Effective Date",
                                         help="The date when the guarantor was hired")
    emp_stop_date = fields.Date(string="Employment Stop Date", help="The date when the guarantor's employment ended")

    """non mandatory fields"""

    guarantor_spouse_name = fields.Char(string="Guarantor Spouse Name")
    guarantor_priorty = fields.Char(string="Guarantor Priority")
    guarantor_emp_id_no = fields.Char(string="Guarantor Employee ID Number")
    guarantor_org_name = fields.Char(string="Guarantor Organization Name")
    guarantor_bilng_flag = fields.Char(string="Guarantor Billing Hold Flag")
    guarantor_credit_code = fields.Char(string="Guarantor Credit Rating Code")
    guarantor_death_flag = fields.Char(string="Guarantor Death Flag")
    guarantor_charg_adjst_code = fields.Char(string="Guarantor Charge Adjustment Code")
    guarantor_annual_incom = fields.Char(string="Guarantor Household Annual Income")
    guarantor_house_siz = fields.Char(string="Guarantor Household Size")
    guarantor_martl_status = fields.Char(string="Guarantor Marital Status Code")
    living_depndency = fields.Char(string="Living Dependency")
    ambulatory_status = fields.Char(string="Ambulatory Status")
    citizenship = fields.Char(string="Citizenship")
    primary_lang = fields.Char(string="Primary Language")
    living_arrangment = fields.Char(string="Living Arrangement")
    publicity_code = fields.Char(string="Publicity Code")
    protection_indicator = fields.Char(string="Protection Indicator")
    student_indicator = fields.Char(string="Student Indicator")
    religion = fields.Char(string="Religion")
    mothr_name = fields.Char(string="Mother's Maiden Name")
    nationality = fields.Many2one('res.country', string='Nationality')
    ethnic_grp = fields.Char(string="Ethnic Group")
    contct_persns_name = fields.Char(string="Contact Person's Name")
    contact_reason = fields.Char(string="Contact Reason")
    contact_relationship = fields.Char(string="Contact Relationship")
    handicap = fields.Boolean(string="Handicap")
    job_status = fields.Char(string="Job Status")
    grntr_financl_class = fields.Char(string="Guarantor Financial Class")
    gratntr_race = fields.Char(string="Guarantor Race")
    gratntr_brth_place = fields.Char(string="Guarantor Birth Place")
    vip_indicatr = fields.Char(string="VIP Indicator")
    contct_persns_contct_no = fields.Integer(string="Contact Person's Telephone Number")
    guarantor_death_date = fields.Datetime(string="Guarantor Death Date And Time")

    state = fields.Selection([('draft', 'Draft'), ('submited', 'Submitted'), ('cancel', 'Cancel')], string='Status',
                             default='draft')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'): vals['name'] = self.env['ir.sequence'].next_by_code(
            'kg.guarantor.segment') or _('New')
        request = super(KgGurantorSegment, self).create(vals)
        return request

    def btn_submit(self):
        self.write({'state': 'submited'})
        url = self.env['ir.config_parameter'].get_param('web.base.url')
        data = {
            'set_id_gt1': self.set_id_gt1,
            'gurantor_number': self.gurantor_number,
            'gurantor_name': self.gurantor_name,
            'gurantor_type': self.gurantor_type,
            'gurantor_relationship':self.gurantor_relationship,
            'gurantor_ssn':self.gurantor_ssn,
            'gurantor_emplyr_name': self.gurantor_emplyr_name,
            'gurantor_emp_status': self.gurantor_emp_status,
            'gurantor_addres': self.gurantor_addres,
            'gurantor_employer_addres': self.gurantor_employer_addres,
            'gurantor_phnno_hom': self.gurantor_phnno_hom,
            'gurantor_phnno_business': self.gurantor_phnno_business,
            'gurantor_employer_phnno': self.gurantor_employer_phnno,
            # 'gurantor_dob': self.gurantor_dob,
            # 'gurantor_start_date': self.gurantor_start_date,
            # 'gurantor_end_date': self.gurantor_end_date,
            'guarantor_administrative_sex': self.guarantor_administrative_sex,
            'gurantor_emp_id_no': self.gurantor_emp_id_no,
            'job_title': self.job_title,
            'job_code': self.job_code,
            'emp_orgnz_name': self.emp_orgnz_name,
            # 'gurantor_hire_eff_date': self.gurantor_hire_eff_date,
            # 'emp_stop_date': self.emp_stop_date,
            'guarantor_spouse_name': self.guarantor_spouse_name,
            'guarantor_priorty': self.guarantor_priorty,
            'guarantor_emp_id_no': self.guarantor_emp_id_no,
            'guarantor_org_name': self.guarantor_org_name,
            'guarantor_bilng_flag': self.guarantor_bilng_flag,
            'guarantor_credit_code': self.guarantor_credit_code,
            'guarantor_death_flag': self.guarantor_death_flag,
            'guarantor_charg_adjst_code': self.guarantor_charg_adjst_code,
            'guarantor_annual_incom': self.guarantor_annual_incom,
            'guarantor_house_siz': self.guarantor_house_siz,
            'guarantor_martl_status': self.guarantor_martl_status,
            'living_depndency': self.living_depndency,
            'ambulatory_status': self.ambulatory_status,
            'citizenship': self.citizenship,
            'primary_lang': self.primary_lang,
            'living_arrangment': self.living_arrangment,
            'publicity_code': self.publicity_code,
            'protection_indicator': self.protection_indicator,
            'student_indicator': self.student_indicator,
            'religion': self.religion,
            'mothr_name': self.mothr_name,
            'nationality': self.nationality.name,
            'ethnic_grp': self.ethnic_grp,
            'contct_persns_name': self.contct_persns_name,
            'contact_reason': self.contact_reason,
            'contact_relationship': self.contact_relationship,
            'handicap': self.handicap,
            'job_status': self.job_status,
            'grntr_financl_class': self.grntr_financl_class,
            'gratntr_race': self.gratntr_race,
            'gratntr_brth_place': self.gratntr_brth_place,
            'vip_indicatr': self.vip_indicatr,
            'contct_persns_contct_no': self.contct_persns_contct_no,
            # 'guarantor_death_date': self.guarantor_death_date,
        }
        response_data = self.env['tdcc.api'].post(data, url)

    def btn_cancel(self):
        print("mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm")
        self.write({'state': 'cancel'})
