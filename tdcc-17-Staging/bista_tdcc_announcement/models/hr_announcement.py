# -*- coding: utf-8 -*-
#
# -*- encoding: utf-8 -*-
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
#

from datetime import datetime
from odoo import models, fields, api


class HrAnnouncementTable(models.Model):
    _name = 'hr.announcement'
    _description = 'HR Announcement'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Announcement Title',
                       required=True, readonly=True)
    state = fields.Selection([('draft', 'Draft'),
                              ('to_approve', 'Waiting For Approval'),
                              ('approved', 'Approved'),
                              ('rejected', 'Refused')], string='Status',
                             default='draft', tracking=True)
    requested_date = fields.Date(string='Requested Date',
                                 default=datetime.now().strftime('%Y-%m-%d'))
    attachment_id = fields.Many2many('ir.attachment', 'doc_warning_rel',
                                     'announcement_doc_id',
                                     'announcement_attach_id',
                                     string="Attachment")
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.user.company_id,
                                 readonly=True,)
    announcement = fields.Html(string='Letter',
                               readonly=True)
    date_start = fields.Date(string='Start Date',
                             default=fields.Date.today(),
                             required=True)
    date_end = fields.Date(string='End Date',
                           default=fields.Date.today(), required=True)

    # @api.multi
    def reject(self):
        self.state = 'rejected'

    # @api.multi
    def approve(self):
        self.state = 'approved'

    # @api.multi
    def sent(self):
        self.state = 'to_approve'
