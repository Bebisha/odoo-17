from odoo import models, fields, api, _
import random
import string


class KgDiagnosis(models.Model):
    _name = 'kg.diagnosis'

    _inherit = ['mail.thread', 'mail.activity.mixin']
    _mail_post_access = 'read'
    _description = 'Kg Diagnosis'

    name = fields.Char(string='Name', copy=False, readonly=True, index=True, default=lambda self: _('New'))
    """mandatory fields"""

    set_id_dg1 = fields.Char(string="Set ID – DG1")
    diag_coding_method = fields.Char(string="Diagnosis Coding Method")
    diag_clinician = fields.Char(string="Diagnosing Clinician")
    diag_priority = fields.Integer(string="Diagnosis Priority",
                                   help="The value 1 means that this is the primary diagnosis. Values 2-99 convey ranked secondary diagnoses")
    diag_code = fields.Char(string="Diagnosis Code – DG1", help="J18.9^Pneumonia, unspecified organism^I10")
    diag_description = fields.Char(string="Diagnosis Description", help="Please provide the diagnosis description")
    diag_date = fields.Datetime(string="Diagnosis Date/Time")
    diag_type = fields.Selection([('A', 'A'), ('W', 'W'), ('F', 'F'), ('O', 'O')],
                                 help="", string="Diagnosis Type")
    diag_action_code = fields.Selection([('Add', 'A'), ('Delete', 'D'), ('Update.', 'U')],
                                        help="A means Add/Insert, D means Delete, and U means update",
                                        string="Diagnosis Action Code")

    """non mandatory fields"""
    major_diag_categry = fields.Char(string="Major Diagnostic Category")
    diag_related_group = fields.Char(string="Diagnostic Related Group")
    drg_approv_indicator = fields.Char(string="DRG Approval Indicator")
    drg_groupr_revw_code = fields.Char(string="DRG Grouper Review Code")
    outlier_type = fields.Char(string="Outlier Type")
    outlier_days = fields.Char(string="Outlier Days")
    outlier_cost = fields.Char(string="Outlier Cost")
    grpr_versn_type = fields.Char(string="Grouper Version And Type")
    diag_classification = fields.Char(string="Diagnosis Classification")
    confidencial_indicatr = fields.Char(string="Confidential Indicator")
    attestation = fields.Char(string="Attestation")
    diag_identifier = fields.Char(string="Diagnosis Identifier")

    state = fields.Selection([('draft', 'Draft'), ('submited', 'Submitted'), ('cancel', 'Cancel')], string='Status',
                             default='draft')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'): vals['name'] = self.env['ir.sequence'].next_by_code(
            'kg.diagnosis') or _('New')
        request = super(KgDiagnosis, self).create(vals)
        return request

    def btn_submit(self):
        self.write({'state': 'submited'})
        url = self.env['ir.config_parameter'].get_param('web.base.url')
        data = {
            'set_id_dg1': self.set_id_dg1,
            'diag_coding_method': self.diag_coding_method,
            'diag_clinician': self.diag_clinician,
            'diag_priority': self.diag_priority,
            'diag_code': self.diag_code,
            'diag_description': self.diag_description,
            # 'diag_date': self.diag_date,
            'diag_type': self.diag_type,
            'diag_action_code': self.diag_action_code,
            'major_diag_categry': self.major_diag_categry,
            'diag_related_group': self.diag_related_group,
            'drg_approv_indicator': self.drg_approv_indicator,
            'drg_groupr_revw_code': self.drg_groupr_revw_code,
            'outlier_type': self.outlier_type,
            'outlier_days': self.outlier_days,
            'outlier_cost': self.outlier_cost,
            'grpr_versn_type': self.grpr_versn_type,
            'diag_classification': self.diag_classification,
            'confidencial_indicatr': self.confidencial_indicatr,
            'attestation': self.attestation,
            'diag_identifier': self.diag_identifier,
        }

        response_data = self.env['tdcc.api'].post(data, url)

    def btn_cancel(self):
        print("mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm")
        self.write({'state': 'cancel'})
