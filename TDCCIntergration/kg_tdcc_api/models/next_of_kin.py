from odoo import models, fields, api, _
import random
import string


class KgNextOfKin(models.Model):
    _name = 'kg.associated.parties'

    _inherit = ['mail.thread', 'mail.activity.mixin']
    _mail_post_access = 'read'
    _description = 'Kg Next Of Kin'

    name = fields.Char(string='Name', copy=False, readonly=True, index=True, default=lambda self: _('New'))
    """mandatory fields"""

    set_id=fields.Char(string="Set ID – NK1")
    first_name=fields.Char(string="First Name")
    relationship=fields.Char(string="Relationship")
    address=fields.Text(string="Address")
    cell_phn_no = fields.Char(string="Cell Phone")
    business_phn_no = fields.Char(string="Business Phone Number")
    emergency_contact = fields.Char(string="Contact Role")
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    organization_name = fields.Char(string="Organization Name – NK1")
    contact_persons_name = fields.Char(string="Contact Person's Name")
    contact_persons_phn_no = fields.Char(string="Contact Person's Telephone Number")

    """non mandatory fields"""

    middle_name = fields.Char(string="Middle Name")
    last_name = fields.Char(string="last Name")
    home_phn_no = fields.Char(string="Home Phone")
    email = fields.Char(string="email")
    nok_job_title = fields.Char(string="Next of Kin/Associated Parties Job Title")
    nok_job_code = fields.Char(string="Next of Kin / Associated Parties Job Code/Class")
    nok_job_emp_no = fields.Char(string="Next of Kin / Associated Parties Employee Number")
    maritual_status = fields.Selection([('married', 'Married'), ('unmarried', 'Unmarried')], default=None,
                                       string="Marital Status")
    administrative_sex = fields.Selection([('male', 'Male'), ('female', 'Female'), ('unknown', 'Unknown')],
                                          default=None,
                                          string="Administrative Sex")
    birth_date = fields.Datetime('Date/Time of Birth')
    living_dependency = fields.Char(string="Living Dependency")
    ambulatory_status = fields.Char(string="Ambulatory Status")
    citizenship = fields.Char(string="Citizenship")
    primary_lang = fields.Many2one('res.lang', string="Primary Language")
    living_arrangement = fields.Char(string="Living Arrangement")
    publicity_code = fields.Selection([('Family', 'F'), ('No Publicity', 'N'), ('Other,', 'O'),
                                       ('Unknown', 'U')],
                                      help="F for Family,N for No Publicity and O for Other,U for  Unknown",
                                      string="Publicity Code")
    protection_indicator = fields.Selection([('Yes', '1'), ('No', '0'), ('not available,', 'None')],
                                            help="1 for Yes,0 for No  and None for Not available",
                                            string="Protection Indicator")

    student_indicator = fields.Char(string="Student Indicator")
    religion = fields.Char(string="Religion")
    mothers_name = fields.Char(string="Mother's Maiden Name")
    nationality = fields.Many2one('res.country', string='Nationality')
    ethnic_group = fields.Char(string="Ethnic Group")
    contact_reason = fields.Char(string="Contact Reason")
    contact_persons_addres = fields.Text(string="Contact Person's Address")
    nok_identifiers= fields.Char(string="Next of Kin/Associated Party's Identifiers")
    job_status= fields.Char(string="Job Status")
    race= fields.Char(string="Race")
    handicap = fields.Boolean(string="Handicap")
    contact_persn_secrty_no = fields.Char(string="Contact Person Social Security Number")
    nok_birth_place = fields.Char(string="Next of Kin Birth Place")
    vip_indicator = fields.Char(string="VIP Indicator")

    state = fields.Selection([('draft', 'Draft'),('submited','Submitted'),('cancel','Cancel')],string='Status', default='draft')


    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'): vals['name'] = self.env['ir.sequence'].next_by_code(
            'kg.associated.parties') or _('New')
        request = super(KgNextOfKin, self).create(vals)
        return request

    def btn_submit(self):
        self.write({'state': 'submited'})
        url = self.env['ir.config_parameter'].get_param('web.base.url')
        data = {
            'set_id' : self.set_id,
            'first_name' : self.first_name,
            'relationship' : self.relationship,
            'address' : self.address,
            'cell_phn_no' : self.cell_phn_no,
            'business_phn_no' : self.business_phn_no,
            'emergency_contact' : self.emergency_contact,
            # 'start_date' : self.start_date,
            # 'end_date' : self.end_date,
            'organization_name' : self.organization_name,
            'contact_persons_name' : self.contact_persons_name,
            'contact_persons_phn_no' : self.contact_persons_phn_no,
            'middle_name' : self.middle_name,
            'last_name' : self.last_name,
            'home_phn_no' : self.home_phn_no,
            'email' : self.email,
            'nok_job_title' : self.nok_job_title,
            'nok_job_code' : self.nok_job_code,
            'nok_job_emp_no' : self.nok_job_emp_no,
            'maritual_status' : self.maritual_status,
            'administrative_sex' : self.administrative_sex,
            # 'birth_date' : self.birth_date,
            'living_dependency' : self.living_dependency,
            'ambulatory_status' : self.ambulatory_status,
            'citizenship' : self.citizenship,
            'primary_lang' : self.primary_lang.name,
            'living_arrangement' : self.living_arrangement,
            'publicity_code' : self.publicity_code,
            'protection_indicator' : self.protection_indicator,
            'student_indicator' : self.student_indicator,
            'religion' : self.religion,
            'mothers_name' : self.mothers_name,
            'nationality' : self.nationality.name,
            'ethnic_group' : self.ethnic_group,
            'contact_reason' : self.contact_reason,
            'contact_persons_addres' : self.contact_persons_addres,
            'nok_identifiers' : self.nok_identifiers,
            'job_status' : self.job_status,
            'race' : self.race,
            'handicap' : self.handicap,
            'contact_persn_secrty_no' : self.contact_persn_secrty_no,
            'nok_birth_place' : self.nok_birth_place,
            'vip_indicator' : self.vip_indicator,

        }
        response_data = self.env['tdcc.api'].post(data, url)

    def btn_cancel(self):
        print("mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm")
        self.write({'state': 'cancel'})