from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class KgPatientIdentification(models.Model):
    _name = "patient.identification"

    administrative_sex = fields.Many2one('gender.form', string="Administrative Sex" ,required= True)
    marital_status = fields.Many2one('marital.status', string="Marital Status" ,required= True)
    religion = fields.Many2one('religion.form', string="Religion" ,required= True)
    nationality = fields.Many2one("nationality.form", string="Nationality" ,required= True)
    emi_id = fields.Char( string='Emirates ID' ,size = 8)
    pass_no = fields.Char(string='Passport No')
    primary_lang = fields.Many2one('primary.language',string='Primary Language' ,required= True)

    patient_identification_id = fields.Many2one('res.partner', string='student')
    patient_profession_id = fields.Many2one('patient.profession', string='PatientProfession')
    last_update_facility = fields.Many2one('appointment.appointment', string='Last Update Facility')
    patient_identifier_list = fields.Char(string="Patient Identifier list", copy=False, index=True, readonly=False,
                                          default=lambda self: _('New'))
    first_name = fields.Char(string="First Name")
    middle_name = fields.Char(string="Middle Name")
    last_name = fields.Char(string="Last Name")

    full_name = fields.Char(string="Name", compute="_compute_full_name", store=True)
    pid_date = fields.Datetime('PID Last Update Date', default=lambda self: fields.Datetime.now())
    birthday = fields.Date(string='Date of Birth')
    patient_death_indicator = fields.Selection([('Yes', 'Y'),
                                                ('No', 'N')], string="Patient Death Indicator", )
    identity_unknown_indicator = fields.Selection([('vip', 'V'), ('tourist', 'T'),
                                                   ('all dubai residents', 'O')], string="Identity Unknown Indicator",
                                                  help="V for VIP,T for Tourist and O for all residents in dubai ",
                                                  )
    living_arrangement = fields.Char(string="Living Arrangement")
    publicity_code = fields.Char(string="Publicity Code")
    protection_indicator = fields.Char(string="Protection Indicator")
    student_indicator = fields.Char(string="Student Indicator")
    employment_status = fields.Selection([('Active', 'A'), ('Inactivate', 'I')],
                                        help="A for ‘Active’ or I for ‘Inactive",
                                        string="Status")


    @api.model
    def create(self, vals):
        if vals.get('patient_identifier_list', _('New')) == _('New'):
            vals['patient_identifier_list'] = self.env['ir.sequence'].next_by_code(
                'patient_identifier') or _('New')
        return super(KgPatientIdentification, self).create(vals)

    @api.depends('first_name', 'middle_name', 'last_name')
    def _compute_full_name(self):
        for record in self:
            last_name = record.last_name or ''
            middle_name = record.middle_name or ''
            first_name = record.first_name or ''

            record.full_name = f"{last_name} {middle_name} {first_name}"




