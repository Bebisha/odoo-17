from odoo import models, fields, api, _
import random
import string


class KgDiagnosisGroupSegmant(models.Model):
    _name = 'kg.diag.group.segment'

    _inherit = ['mail.thread', 'mail.activity.mixin']
    _mail_post_access = 'read'
    _description = 'Kg Diagnosis Related Group Segment'

    name = fields.Char(string='Name', copy=False, readonly=True, index=True, default=lambda self: _('New'))
    """mandatory fields"""

    diag_reltd_grp = fields.Char(string="Diagnostic Related Group")
    drg_assigned_date = fields.Datetime(string="DRG Assigned Date/Time")
    drg_approvl_indicator = fields.Char(string="DRG Approval Indicator")
    drg_grpr_revw_code = fields.Char(string="DRG Grouper Review Code")
    outlier_type = fields.Char(string="Outlier Type")
    outlier_days = fields.Char(string="Outlier Days")
    outlier_cost = fields.Char(string="Outlier Cost")
    drg_payor = fields.Char(string="DRG Payor")
    outlier_reimbursment = fields.Char(string="Outlier Reimbursement")
    confidential_indicator = fields.Char(string="Confidential Indicator")
    drg_transfer_type = fields.Char(string="DRG Transfer Type")

    """non mandatory fields"""

    state = fields.Selection([('draft', 'Draft'), ('submited', 'Submitted'), ('cancel', 'Cancel')], string='Status',
                             default='draft')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'): vals['name'] = self.env['ir.sequence'].next_by_code(
            'kg.diag.group.segment') or _('New')
        request = super(KgDiagnosisGroupSegmant, self).create(vals)
        return request

    def btn_submit(self):
        self.write({'state': 'submited'})
        url = self.env['ir.config_parameter'].get_param('web.base.url')
        data = {
            'diag_reltd_grp': self.diag_reltd_grp,
            # 'drg_assigned_date': self.drg_assigned_date,
            'drg_approvl_indicator': self.drg_approvl_indicator,
            'drg_grpr_revw_code': self.drg_grpr_revw_code,
            'outlier_type': self.outlier_type,
            'outlier_days': self.outlier_days,
            'outlier_cost': self.outlier_cost,
            'drg_payor': self.drg_payor,
            'outlier_reimbursment': self.outlier_reimbursment,
            'confidential_indicator': self.confidential_indicator,
            'drg_transfer_type': self.drg_transfer_type,

        }
        response_data = self.env['tdcc.api'].post(data, url)

    def btn_cancel(self):
        print("mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm")
        self.write({'state': 'cancel'})
