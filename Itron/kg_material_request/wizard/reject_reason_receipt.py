# -*- coding: utf-8 -*-
from markupsafe import Markup
from odoo import models, fields, _


class RejectReasonReceipt(models.TransientModel):
    _name = 'rejects.reason.receipt'
    _description = 'Receipt Request Reject Reason'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    reject_reason = fields.Text(string="Reason")
    receipt_id = fields.Many2one('stock.picking',string="Material Id")

    def confirm_reject_reason(self):
        if self.reject_reason:
            self.receipt_id.reject_reason = self.reject_reason
            self.receipt_id.rejected_by = self.env.user.id
            # self.receipt_id.reject_date = fields.Date.today()
        self.receipt_id.is_reject = True

