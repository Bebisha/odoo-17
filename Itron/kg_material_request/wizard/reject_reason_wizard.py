# -*- coding: utf-8 -*-
from markupsafe import Markup
from odoo import models, fields, _


class RejectReasonWizard(models.TransientModel):
    _name = 'rejects.reason.wizard'
    _description = 'Material Request Reject Reason'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    reject_reason = fields.Text(string="Reason")
    material_id = fields.Many2one('kg.material.request',string="Material Id")

    def confirm_reject_reason(self):
        if self.reject_reason:
            self.material_id.reject_reason = self.reject_reason
            self.material_id.rejected_by = self.env.user.id
            self.material_id.reject_date = fields.Date.today()
        self.material_id.state = 'reject'
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }





