from odoo import models, fields, api, _
import random
import string


class kgInsurance(models.Model):
    _name = 'kg.insurance'

    _inherit = ['mail.thread', 'mail.activity.mixin']
    _mail_post_access = 'read'
    _description = 'Kg Insurance '

    name = fields.Char(string='Name', copy=False, readonly=True, index=True, default=lambda self: _('New'))
    """mandatory fields"""

    set_id_in1 = fields.Char(string="Set ID – IN1")
    health_plan_id = fields.Char(string="Health Plan ID")
    insurence_compny_id = fields.Char(string="Insurance Company ID")
    insurence_compny_name = fields.Char(string="Insurance Company Name")
    insurence_compny_address = fields.Char(string="Insurance Company Address")
    insurence_contact_person = fields.Char(string="Insurance Co Contact Person")
    plan_type = fields.Char(string="Plan Type")
    insured_name = fields.Char(string="Name Of Insured")
    insured_relationship_patent = fields.Char(string="Insured's Relationship To Patient")
    insured_address = fields.Char(string="Insured's Address")
    cord_priorty = fields.Char(string="Coord of Ben. Priority", help="Values are: 1, 2, 3, etc")
    insurence_co_phn = fields.Integer(string="Insurance Co Phone Number")
    group_no = fields.Integer(string="Group Number")
    group_name = fields.Char(string="Group Name")
    policy_no = fields.Char(string="Policy Number", help="Membership Number or Policy Number")
    plan_effctv_date = fields.Date(string="Plan Effective Date")
    plan_expiry_date = fields.Date(string="Plan Expiration Date")

    """non mandatory fields"""

    insured_grp_empid = fields.Char(string="Insured's Group Emp ID")
    insured_grp_emp_name = fields.Char(string="Insured's Group Emp Name")
    authorizatn_info = fields.Char(string="Authorization Information")
    insured_dob = fields.Date(string="Insured's Date Of Birth")
    assign_benft = fields.Char(string="Assignment Of Benefits")
    cordination_benft = fields.Char(string="Coordination Of Benefits")
    notice_addmsn_flag = fields.Char(string="Notice Of Admission Flag")
    notice_addmsn_date = fields.Date(string="Notice Of Admission Date")
    report_elgblty_flag = fields.Char(string="Report Of Eligibility Flag")
    report_elgblty_date = fields.Date(string="Report Of Eligibility Date")
    verification_date = fields.Datetime(string="Verification Date/Time")
    release_info_code = fields.Char(string="Release Information Code")
    pre_admit_cert = fields.Char(string="Pre-Admit Cert (PAC)")
    verifction_by = fields.Char(string="Verification By")
    typ_agrmnt_code = fields.Char(string="Type Of Agreement Code")
    billing_stats = fields.Char(string="Billing Status")
    liftime_resrv_day = fields.Char(string="Lifetime Reserve Days")
    delay_befr_day = fields.Char(string="Delay Before L.R. Day")
    compny_plan_code = fields.Char(string="Company Plan Code")
    plan_deductble = fields.Char(string="Policy Deductible")
    plan_limit_amnt = fields.Char(string="Policy Limit – Amount")
    plan_limit_days = fields.Char(string="Policy Limit – Days")
    room_rate = fields.Char(string="Room Rate – Semi-Private")
    room_rate_prvt = fields.Char(string="Room Rate – Private")
    insured_emplmnt_status = fields.Char(string="Insured's Employment Status")
    verificatn_status = fields.Char(string="Verification Status")
    insurence_plan_id = fields.Char(string="Prior Insurance Plan ID")
    coverage_type = fields.Char(string="Coverage Type")
    handicap = fields.Boolean(string="Handicap")
    insured_id_no = fields.Char(string="Insured's ID Number")
    sign_code = fields.Char(string="Signature Code")
    insured_birth_place = fields.Char(string="Insured's Birth Place")
    vip_indctor = fields.Char(string="VIP Indicator")
    sign_code_date = fields.Date(string="Signature Code Date")
    insured_employr_addrs = fields.Text(string="Insured's Employer's Address")
    administrative_sex = fields.Selection([('male', 'Male'), ('female', 'Female'), ('unknown', 'Unknown')],
                                          default=None,
                                          string="Insured's Administrative Sex")
    state = fields.Selection([('draft', 'Draft'), ('submited', 'Submitted'), ('cancel', 'Cancel')], string='Status',
                             default='draft')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'): vals['name'] = self.env['ir.sequence'].next_by_code(
            'kg.insurance') or _('New')
        request = super(kgInsurance, self).create(vals)
        return request

    def btn_submit(self):
        self.write({'state': 'submited'})
        url = self.env['ir.config_parameter'].get_param('web.base.url')
        data = {
            'set_id_in1': self.set_id_in1,
            'health_plan_id': self.health_plan_id,
            'insurence_compny_id': self.insurence_compny_id,
            'insurence_compny_name': self.insurence_compny_name,
            'insurence_compny_address': self.insurence_compny_address,
            'insurence_contact_person': self.insurence_contact_person,
            'plan_type': self.plan_type,
            'insured_name': self.insured_name,
            'insured_relationship_patent': self.insured_relationship_patent,
            'insured_address': self.insured_address,
            'cord_priorty': self.cord_priorty,
            'insurence_co_phn': self.insurence_co_phn,
            'group_no': self.group_no,
            'group_name': self.group_name,
            'policy_no': self.policy_no,
            # 'plan_effctv_date': self.plan_effctv_date,
            # 'plan_expiry_date': self.plan_expiry_date,
            'insured_grp_empid': self.insured_grp_empid,
            'insured_grp_emp_name': self.insured_grp_emp_name,
            'authorizatn_info': self.authorizatn_info,
            'insured_dob': self.insured_dob,
            'assign_benft': self.assign_benft,
            'cordination_benft': self.cordination_benft,
            'notice_addmsn_flag': self.notice_addmsn_flag,
            # 'notice_addmsn_date': self.notice_addmsn_date,
            'report_elgblty_flag': self.report_elgblty_flag,
            # 'report_elgblty_date': self.report_elgblty_date,
            # 'verification_date': self.verification_date,
            'release_info_code': self.release_info_code,
            'pre_admit_cert': self.pre_admit_cert,
            'verifction_by': self.verifction_by,
            'typ_agrmnt_code': self.typ_agrmnt_code,
            'billing_stats': self.billing_stats,
            'liftime_resrv_day': self.liftime_resrv_day,
            'delay_befr_day': self.delay_befr_day,
            'compny_plan_code': self.compny_plan_code,
            'plan_deductble': self.plan_deductble,
            'plan_limit_amnt': self.plan_limit_amnt,
            'plan_limit_days': self.plan_limit_days,
            'room_rate': self.room_rate,
            'room_rate_prvt': self.room_rate_prvt,
            'insured_emplmnt_status': self.insured_emplmnt_status,
            'verificatn_status': self.verificatn_status,
            'insurence_plan_id': self.insurence_plan_id,
            'coverage_type': self.coverage_type,
            'handicap': self.handicap,
            'insured_id_no': self.insured_id_no,
            'sign_code': self.sign_code,
            'insured_birth_place': self.insured_birth_place,
            'vip_indctor': self.vip_indctor,
            # 'sign_code_date': self.sign_code_date,
            'insured_employr_addrs': self.insured_employr_addrs,
            'administrative_sex': self.administrative_sex,
        }
        response_data = self.env['tdcc.api'].post(data, url)

    def btn_cancel(self):
        print("mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm")
        self.write({'state': 'cancel'})
