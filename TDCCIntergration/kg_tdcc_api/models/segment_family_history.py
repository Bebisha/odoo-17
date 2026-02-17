from odoo import models, fields, api, _
import random
import string

class kgSegmentFamilyHistory(models.Model):
    _name = 'kg.segment.family.history'

    _inherit = ['mail.thread', 'mail.activity.mixin']
    _mail_post_access = 'read'
    _description = 'Kg Segment Family History'

    name = fields.Char(string='Name', copy=False, readonly=True, index=True, default=lambda self: _('New'))

    """mandatory fields"""

    set_id_zfh = fields.Selection([('Delete', 'D'), ('Inactivate', 'I')], help="D = Delete, I = Inactivate",
                                        string="SetID – ZFH")
    status = fields.Selection([('Active', 'A'), ('Inactivate', 'I')],
                                        help="A for ‘Active’ or I for ‘Inactive",
                                        string="Status")
    from_date = fields.Date(string="From Time",help="Beginning of period covered")
    to_date = fields.Date(string="To Time",help="End of period covered")
    family_member = fields.Char(string="Family Member",help="Family Member Covered")
    diagnosis = fields.Char(string="Diagnosis",help="Diagnosis on family member")
    note_text = fields.Char(string="Note Text",help="Length subject to the total streamlet size limit - 3,000,000")
    entered_by = fields.Char(string="Entered By",help="User name")


    """non mandatory fields"""

    state = fields.Selection([('draft', 'Draft'),('submited','Submitted'),('cancel','Cancel')],string='Status', default='draft')


    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'): vals['name'] = self.env['ir.sequence'].next_by_code(
            'kg.segment.family.history') or _('New')
        request = super(kgSegmentFamilyHistory, self).create(vals)
        return request

    def btn_submit(self):
        self.write({'state': 'submited'})
        url = self.env['ir.config_parameter'].get_param('web.base.url')
        data = {
            'set_id_zfh': self.set_id_zfh,
            'status': self.status,
            # 'from_date': self.from_date,
            # 'to_date': self.to_date,
            'family_member': self.family_member,
            'diagnosis': self.diagnosis,
            'note_text': self.note_text,
            'entered_by': self.entered_by,

        }
        response_data = self.env['tdcc.api'].post(data, url)

    def btn_cancel(self):
        print("mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm")
        self.write({'state': 'cancel'})