from odoo import models, fields, api, _
import random
import string

class kgSegmentSocialHistory(models.Model):
    _name = 'kg.segment.social.history'

    _inherit = ['mail.thread', 'mail.activity.mixin']
    _mail_post_access = 'read'
    _description = 'Kg Segment Social History'

    name = fields.Char(string='Name', copy=False, readonly=True, index=True, default=lambda self: _('New'))

    """mandatory fields"""

    set_id_zsh = fields.Selection([('Delete', 'D'), ('Inactivate', 'I')],
                                        help="D = Delete, I = Inactivate",
                                        string="SetID – ZSH")
    status = fields.Selection([('Active', 'Active'), ('Inactivate', 'Inactivate')],
                                        help="Status of history (Active, Inactive, To be Confirmed",
                                        string="Status")
    from_date = fields.Date(string="From Time",help="Beginning of period covered")
    to_date = fields.Date(string="To Time",help="End of period covered")

    social_habit = fields.Char(string="Social Habit",help="Social Habit Code--- Smoking")
    social_habit_qty = fields.Char(string="Social Habit Qty",help="Quantity associated with social habit")
    social_habit_categry = fields.Char(string="Social Habit Category",help="Stores coded type of social habit")
    social_habit_comments = fields.Char(string="Social Habit Comments",help="Length subject to the total streamlet size limit - 3,000,000")
    entered_by = fields.Char(string="Entered By",help="User name")


    """non mandatory fields"""

    state = fields.Selection([('draft', 'Draft'),('submited','Submitted'),('cancel','Cancel')],string='Status', default='draft')


    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'): vals['name'] = self.env['ir.sequence'].next_by_code(
            'kg.segment.social.history') or _('New')
        request = super(kgSegmentSocialHistory, self).create(vals)
        return request

    def btn_submit(self):
        self.write({'state': 'submited'})
        url = self.env['ir.config_parameter'].get_param('web.base.url')
        data = {
            'set_id_zsh': self.set_id_zsh,
            'status': self.status,
            # 'from_date': self.from_date,
            # 'to_date': self.to_date,
            'social_habit': self.social_habit,
            'social_habit_qty': self.social_habit_qty,
            'social_habit_categry': self.social_habit_categry,
            'social_habit_comments': self.social_habit_comments,
            'entered_by': self.entered_by,

        }
        response_data = self.env['tdcc.api'].post(data, url)

    def btn_cancel(self):
        print("mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm")
        self.write({'state': 'cancel'})