from odoo import models, fields, api, _
import random
import string

class KgPatientAllergyInfo(models.Model):
    _name = 'kg.patient.allergy.info'

    _inherit = ['mail.thread', 'mail.activity.mixin']
    _mail_post_access = 'read'
    _description = 'Kg Patient Allergy Information'

    name = fields.Char(string='Name', copy=False, readonly=True, index=True, default=lambda self: _('New'))
    """mandatory fields"""

    set_id_al1= fields.Char(string="Set ID – AL1")
    allergy_type_code= fields.Char(string="Allergen Type Code", help="value must be sent as FA that means Food allergy,CA for cheese allergy")
    allergy_code_descrptn= fields.Char(string="Allergen Code/Mnemon ic/Description", help="value must be sent as 300914000^cheese allergy")
    allergy_severty_code= fields.Char(string="Allergy Severity Code", help="Please use HL7-Health Level Seven codes here")
    allergy_reaction_code= fields.Char(string="Allergy Reaction Code", help="Please use EMR-Electronic Medical Record to provide the reaction code ")
    identification_date= fields.Date(string="Identification Date", help="Date when allergy was discovered")


    # allergy_type_code = fields.Selection([('da', 'DA'), ('fa', 'FA'), ('ma', 'MA'), ('mc', 'MC'),('', 'EA'),('O', 'AA'),('P', 'PA'),('R', 'LA'),
    #                                               ('S', 'OT')],
    #                                         help="",
    #                                         string="Allergen Type Code")

    state = fields.Selection([('draft', 'Draft'),('submited','Submitted'),('cancel','Cancel')],string='Status', default='draft')


    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'): vals['name'] = self.env['ir.sequence'].next_by_code(
            'kg.patient.allergy.info') or _('New')
        request = super(KgPatientAllergyInfo, self).create(vals)
        return request

    def btn_submit(self):
        self.write({'state': 'submited'})
        url = self.env['ir.config_parameter'].get_param('web.base.url')
        data = {
            'set_id_al1' : self.set_id_al1,
            'allergy_type_code' : self.allergy_type_code,
            'allergy_code_descrptn' : self.allergy_code_descrptn,
            'allergy_severty_code' : self.allergy_severty_code,
            'allergy_reaction_code' : self.allergy_reaction_code,
            # 'identification_date' : self.identification_date,

        }
        response_data = self.env['tdcc.api'].post(data, url)


    def btn_cancel(self):
        print("mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm")
        self.write({'state': 'cancel'})