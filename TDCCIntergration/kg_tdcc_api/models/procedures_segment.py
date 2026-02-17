from odoo import models, fields, api, _
import random
import string


class KgProceduresSegment(models.Model):
    _name = 'kg.procedures.segment'

    _inherit = ['mail.thread', 'mail.activity.mixin']
    _mail_post_access = 'read'
    _description = 'Kg Procedures Segment'

    name = fields.Char(string='Name', copy=False, readonly=True, index=True, default=lambda self: _('New'))
    """mandatory fields"""

    set_id_pr1 = fields.Char(string="Set ID – PR1")
    procedure_coding_method = fields.Char(string="Procedure Coding Method")
    procedure_cod = fields.Char(string="Procedure Code")
    procedure_description = fields.Char(string="Procedure Description")
    procedure_date = fields.Datetime(string="Procedure Date/Time")
    surgeon = fields.Char(string="Surgeon")
    procedure_identifier = fields.Char(string="Procedure Identifier")
    procedure_action_code = fields.Char(string="Procedure Action Code",
                                        help="D = Delete, C = Clear/Delete All, Any other value = Add or Update")

    """non mandatory fields"""
    procedr_functional_type = fields.Char(string="Procedure Functional Type")
    procedr_minutes = fields.Char(string="Procedure Minutes")
    anasthesiologist = fields.Char(string="Anesthesiologist")
    anasthesia_code = fields.Char(string="Anesthesia Code")
    anasthesia_minutes = fields.Char(string="Anesthesia Minutes")
    procedr_practitionr = fields.Char(string="Procedure Practitioner")
    consent_code = fields.Char(string="Consent Code")
    associated_code = fields.Char(string="Associated Diagnosis Code")
    procedure_code_modifr = fields.Char(string="Procedure Code Modifier")
    procedure_drug_type = fields.Char(string="Procedure DRG Type")
    tissue_type_code = fields.Char(string="Tissue Type Code")
    procedure_priority = fields.Integer(string="Procedure Priority",
                                        help="The value 1 means that this is the primary procedure and values 2-99 convey ranked secondary procedures")

    state = fields.Selection([('draft', 'Draft'), ('submited', 'Submitted'), ('cancel', 'Cancel')], string='Status',
                             default='draft')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'): vals['name'] = self.env['ir.sequence'].next_by_code(
            'kg.procedures.segment') or _('New')
        request = super(KgProceduresSegment, self).create(vals)
        return request

    def btn_submit(self):
        self.write({'state': 'submited'})
        url = self.env['ir.config_parameter'].get_param('web.base.url')
        data = {
            'set_id_pr1': self.set_id_pr1,
            'procedure_coding_method': self.procedure_coding_method,
            'procedure_cod': self.procedure_cod,
            'procedure_description': self.procedure_description,
            # 'procedure_date': self.procedure_date,
            'surgeon': self.surgeon,
            'procedure_identifier': self.procedure_identifier,
            'procedure_action_code': self.procedure_action_code,
            'procedr_functional_type': self.procedr_functional_type,
            'procedr_minutes': self.procedr_minutes,
            'anasthesiologist': self.anasthesiologist,
            'anasthesia_code': self.anasthesia_code,
            'anasthesia_minutes': self.anasthesia_minutes,
            'procedr_practitionr': self.procedr_practitionr,
            'consent_code': self.consent_code,
            'associated_code': self.associated_code,
            'procedure_code_modifr': self.procedure_code_modifr,
            'procedure_drug_type': self.procedure_drug_type,
            'tissue_type_code': self.tissue_type_code,
            'procedure_priority': self.procedure_priority,
        }
        response_data = self.env['tdcc.api'].post(data, url)

    def btn_cancel(self):
        print("mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm")
        self.write({'state': 'cancel'})
