from odoo import models, fields, api, _
import random
import string


class KgPatientDemographic(models.Model):
    _name = 'kg.patient.demographic'

    _inherit = ['mail.thread', 'mail.activity.mixin']
    _mail_post_access = 'read'
    _description = 'Kg Patient Demographic'

    name = fields.Char(string='Name', copy=False, readonly=True, index=True, default=lambda self: _('New'))
    """"mandatory fields"""

    living_dependency=fields.Char(string="Living Dependency")
    living_arrangement=fields.Char(string="Living Arrangement")
    patient_primary_facilty=fields.Char(string="Patient Primary Facility")
    primary_care_provider=fields.Text(string="Patient Primary Care Provider Name & ID No")
    student_indicator = fields.Char(string="Student Indicator")
    handicap = fields.Boolean(string="Handicap")
    living_will_code = fields.Char(string="Living Will Code")
    organ_donor_code = fields.Char(string="Organ Donor Code")
    seperate_bill = fields.Boolean(string="Separate Bill")
    duplicate_patient = fields.Char(string="Duplicate Patient")
    publicity_code = fields.Selection([('Family', 'F'),('No Publicity', 'N'),('Other,', 'O'),
                                              ('Unknown', 'U')], help="F for Family,N for No Publicity and O for Other,U for  Unknown", string="Publicity Code")
    protection_indicator = fields.Selection([('Yes', '1'), ('No', '0'), ('not available,', 'None')],
                                            help="1 for Yes,0 for No  and None for Not available",string="Protection Indicator")
    effective_date = fields.Date('Protection Indicator Effective Date')

    """"non mandatory fields"""

    place_worship = fields.Char(string="Place of Worship")
    directive_code = fields.Char(string="Advance Directive Code")
    immun_registry_status = fields.Selection([('Active', 'A'), ('Inactive', 'I')],
                                      help="A for Active,I for Inactive",
                                      string="Immunization Registry Status")
    immun_registry_effective_date = fields.Date('Immunization Registry Status Effective Date')
    publicity_code_effective_date = fields.Date('Publicity Code Effective Date')
    military_branch = fields.Char(string="Military Branch")
    military_rank = fields.Char(string="Military Rank/Grade")
    military_status = fields.Char(string="Military Status")

    state = fields.Selection([('draft', 'Draft'),('submited','Submitted'),('cancel','Cancel')],string='Status', default='draft')


    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'): vals['name'] = self.env['ir.sequence'].next_by_code(
            'kg.patient.demographic') or _('New')
        request = super(KgPatientDemographic, self).create(vals)
        return request

    def btn_submit(self):
        self.write({'state': 'submited'})
        url = self.env['ir.config_parameter'].get_param('web.base.url')
        data = {
            'living_dependency' : self.living_dependency,
            'living_arrangement' : self.living_arrangement,
            'patient_primary_facilty' : self.patient_primary_facilty,
            'primary_care_provider' : self.primary_care_provider,
            'student_indicator' : self.student_indicator,
            'handicap' : self.handicap,
            'living_will_code' : self.living_will_code,
            'organ_donor_code' : self.organ_donor_code,
            'seperate_bill' : self.seperate_bill,
            'duplicate_patient' : self.duplicate_patient,
            'publicity_code' : self.publicity_code,
            'protection_indicator' : self.protection_indicator,
            # 'effective_date' : self.effective_date,
            'place_worship' : self.place_worship,
            'directive_code' : self.directive_code,
            'immun_registry_status' : self.immun_registry_status,
            # 'immun_registry_effective_date' : self.immun_registry_effective_date,
            # 'publicity_code_effective_date' : self.publicity_code_effective_date,
            'military_branch' : self.military_branch,
            'military_rank' : self.military_rank,
            'military_status' : self.military_status
        }
        response_data = self.env['tdcc.api'].post(data, url)

    def btn_cancel(self):
        self.write({'state': 'cancel'})