from odoo import models, fields, api, _
import random
import string


class KgPatientMerge(models.Model):
    _name = 'kg.patient.merge'

    _inherit = ['mail.thread', 'mail.activity.mixin']
    _mail_post_access = 'read'
    _description = 'Kg Patient Merge '

    name = fields.Char(string='Name', copy=False, readonly=True, index=True, default=lambda self: _('New'))

    """mandatory fields"""

    patient_identifier_list = fields.Char(string="Prior Patient Identifier List",
                                          help="Contains the PatientNumbers for the victim or source patient record")
    prior_visit_no = fields.Char(string="Prior Visit Number", help="Prior Encounter number")

    """non mandatory fields"""

    pror_alterntv_patient_id = fields.Char(string="Prior Alternate Patient ID")
    pror_patient_account_no = fields.Char(string="Prior Patient Account Number")
    pror_patient_id = fields.Char(string="Prior Patient ID")
    pror_alterntv_visit_id = fields.Char(string="Prior Alternate Visit ID")
    pror_patient_name = fields.Char(string="Prior Patient Name")

    state = fields.Selection([('draft', 'Draft'), ('submited', 'Submitted'), ('cancel', 'Cancel')], string='Status',
                             default='draft')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'): vals['name'] = self.env['ir.sequence'].next_by_code(
            'kg.patient.merge') or _('New')
        request = super(KgPatientMerge, self).create(vals)
        return request

    def btn_submit(self):
        self.write({'state': 'submited'})
        url = self.env['ir.config_parameter'].get_param('web.base.url')
        data = {
            'patient_identifier_list': self.patient_identifier_list,
            'prior_visit_no': self.prior_visit_no,
            'pror_alterntv_patient_id': self.pror_alterntv_patient_id,
            'pror_patient_account_no': self.pror_patient_account_no,
            'pror_patient_id': self.pror_patient_id,
            'pror_alterntv_visit_id': self.pror_alterntv_visit_id,
            'pror_patient_name': self.pror_patient_name,

        }
        response_data = self.env['tdcc.api'].post(data, url)

    def btn_cancel(self):
        print("mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm")
        self.write({'state': 'cancel'})
