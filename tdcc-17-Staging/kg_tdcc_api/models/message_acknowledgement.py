from odoo import models, fields, api, _
import random
import string

class KgMessageAcknowledgement(models.Model):
    _name = 'kg.message.acknowledgement'

    _inherit = ['mail.thread', 'mail.activity.mixin']
    _mail_post_access = 'read'
    _description = 'Kg Message Acknowledgement'

    name = fields.Char(string='Name', copy=False, readonly=True, index=True, default=lambda self: _('New'))

    """mandatory fields"""

    acknwldgmnt_code = fields.Selection([('Application Accept', 'AA'), ('Application Error', 'AE'), ('Application Reject', 'AR')],
                                        help="AA – Application Accept AE – Application Error AR – Application Reject",
                                        string="Acknowledgment Code")
    message_cntrl_id = fields.Char(string="Message Control ID",help="Message control ID of the message sent by the sending system")
    text_message = fields.Char(string="Text Message",help="Describes an error condition")
    expctd_seqnc_no = fields.Char(string="Expected Sequence Number",help="Optional numeric field")
    delayed_acknw_type = fields.Char(string="Delayed Acknowledgment Type",help="Optional numeric field")
    error_condition = fields.Char(string="Error Condition",help="Message Error Condition Codes")

    """non mandatory fields"""




    state = fields.Selection([('draft', 'Draft'),('submited','Submitted'),('cancel','Cancel')],string='Status', default='draft')


    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'): vals['name'] = self.env['ir.sequence'].next_by_code(
            'kg.message.acknowledgement') or _('New')
        request = super(KgMessageAcknowledgement, self).create(vals)
        return request

    def btn_submit(self):
        self.write({'state': 'submited'})
        url = self.env['ir.config_parameter'].get_param('web.base.url')
        data = {
            'acknwldgmnt_code': self.acknwldgmnt_code,
            'message_cntrl_id': self.message_cntrl_id,
            'text_message': self.text_message,
            'expctd_seqnc_no': self.expctd_seqnc_no,
            'delayed_acknw_type': self.delayed_acknw_type,
            'error_condition': self.error_condition,

        }
        response_data = self.env['tdcc.api'].post(data, url)

    def btn_cancel(self):
        print("mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm")
        self.write({'state': 'cancel'})