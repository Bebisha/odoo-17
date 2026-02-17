from odoo import models, fields, api, _
import random
import string


class KgCommonOrder(models.Model):
    _name = 'kg.common.order'

    _inherit = ['mail.thread', 'mail.activity.mixin']
    _mail_post_access = 'read'
    _description = 'Kg Common Order'

    name = fields.Char(string='Name', copy=False, readonly=True, index=True, default=lambda self: _('New'))

    """mandatory fields"""

    order_control = fields.Char(string="Order Control", help="EMR to send the order control code")
    placer_order_no = fields.Char(string="Placer Order Number")
    filler_order_no = fields.Char(string="Filler Order Number")
    order_status = fields.Char(string="Order Status")
    quality_timing = fields.Datetime(string="Quality/Timing")
    transaction_date = fields.Datetime(string="Date / Time of Transaction")
    entered_by = fields.Char(string="Entered By")
    verified_by = fields.Char(string="Verified By")
    ordering_provider = fields.Char(string="Ordering Provider")
    enterers_location = fields.Char(string="Enterer’s Location")
    ordering_facilty_name = fields.Char(string="Ordering Facility Name")
    calbck_phn_no = fields.Integer(string="Call Back Phone Number")
    orderng_fcltyphn_no = fields.Integer(string="Ordering Facility Phone Number")
    ordering_faclty_adrs = fields.Text(string="Ordering Facility Address")
    confidentialty_code = fields.Char(string="Confidentiality Code")
    order_type = fields.Char(string="Order Type", help="EMR to use allowed values here from LAB, MED, OBS, RAD, VXU")

    """non mandatory fields"""

    placer_group_no = fields.Char(string="Placer Group Number")
    response_flag = fields.Char(string="Response Flag")
    parent = fields.Char(string="Parent")
    order_cntrl_code_reasn = fields.Char(string="Order Control Code Reason")
    entering_orgnz = fields.Char(string="Entering Organization")
    entering_device = fields.Char(string="Entering Device")
    action_by = fields.Char(string="Action By")
    advnc_benifcry_notc_code = fields.Char(string="Advanced Beneficiary Notice Code")
    order_effctve_date = fields.Datetime(string="Order Effective Date / Time")
    fillers_avail_date = fields.Datetime(string="Filler’s Expected Availability Date / Time")
    orderng_provider_addrs = fields.Text(string="Ordering Provider Address")
    order_stats_modifr = fields.Char(string="Order Status Modifier")
    overde_reason = fields.Char(string="Advanced Beneficiary Notice Override Reason")
    authrztn_mode = fields.Char(string="Enterer Authorization Mode")
    parent_universal_idntifr = fields.Char(string="Parent Universal Service Identifier")

    state = fields.Selection([('draft', 'Draft'), ('submited', 'Submitted'), ('cancel', 'Cancel')], string='Status',
                             default='draft')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'): vals['name'] = self.env['ir.sequence'].next_by_code(
            'kg.common.order') or _('New')
        request = super(KgCommonOrder, self).create(vals)
        return request

    def btn_submit(self):
        self.write({'state': 'submited'})
        url = self.env['ir.config_parameter'].get_param('web.base.url')
        data = {
            'order_control': self.order_control,
            'placer_order_no': self.placer_order_no,
            'filler_order_no': self.filler_order_no,
            'order_status': self.order_status,
            # 'quality_timing': self.quality_timing,
            # 'transaction_date': self.transaction_date,
            'entered_by': self.entered_by,
            'verified_by': self.verified_by,
            'ordering_provider': self.ordering_provider,
            'enterers_location': self.enterers_location,
            'ordering_facilty_name': self.ordering_facilty_name,
            'calbck_phn_no': self.calbck_phn_no,
            'orderng_fcltyphn_no': self.orderng_fcltyphn_no,
            'ordering_faclty_adrs': self.ordering_faclty_adrs,
            'confidentialty_code': self.confidentialty_code,
            'order_type': self.order_type,
            'placer_group_no': self.placer_group_no,
            'response_flag': self.response_flag,
            'parent': self.parent,
            'order_cntrl_code_reasn': self.order_cntrl_code_reasn,
            'entering_orgnz': self.entering_orgnz,
            'entering_device': self.entering_device,
            'action_by': self.action_by,
            'advnc_benifcry_notc_code': self.advnc_benifcry_notc_code,
            # 'order_effctve_date': self.order_effctve_date,
            # 'fillers_avail_date': self.fillers_avail_date,
            'orderng_provider_addrs': self.orderng_provider_addrs,
            'order_stats_modifr': self.order_stats_modifr,
            'overde_reason': self.overde_reason,
            'authrztn_mode': self.authrztn_mode,
            'parent_universal_idntifr': self.parent_universal_idntifr,
        }
        response_data = self.env['tdcc.api'].post(data, url)

    def btn_cancel(self):
        print("mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm")
        self.write({'state': 'cancel'})
