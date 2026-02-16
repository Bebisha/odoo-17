from odoo import models, fields, api, _
import random
import string

class KgSegmentConsent(models.Model):
    _name = 'kg.segment.consent'

    _inherit = ['mail.thread', 'mail.activity.mixin']
    _mail_post_access = 'read'
    _description = 'Kg Segment Consent'

    name = fields.Char(string='Name', copy=False, readonly=True, index=True, default=lambda self: _('New'))

    """mandatory fields"""

    output_flag = fields.Selection([('Facility', '1'), ('Global Opt Out', '2')],
                                        help="1 for Facility and 2 for Global Opt Out",
                                        string="OptOutFlag")
    output_flag_date = fields.Date(string="OptOutFlag Entered Date")
    vip_flag_date = fields.Date(string="VIPFlag Entered Date")
    vip_flag = fields.Char(string="VIPFlag",help="VIP Flag Boolean value")


    """non mandatory fields"""

    state = fields.Selection([('draft', 'Draft'),('submited','Submitted'),('cancel','Cancel')],string='Status', default='draft')


    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'): vals['name'] = self.env['ir.sequence'].next_by_code(
            'kg.segment.consent') or _('New')
        request = super(KgSegmentConsent, self).create(vals)
        return request

    def btn_submit(self):
        self.write({'state': 'submited'})
        url = self.env['ir.config_parameter'].get_param('web.base.url')
        data = {
            'output_flag': self.output_flag,
            # 'output_flag_date': self.output_flag_date,
            # 'vip_flag_date': self.vip_flag_date,
            'vip_flag': self.vip_flag,
        }
        response_data = self.env['tdcc.api'].post(data, url)
        print('yyyyyyyy', response_data)

    def btn_cancel(self):
        print("mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm")
        self.write({'state': 'cancel'})