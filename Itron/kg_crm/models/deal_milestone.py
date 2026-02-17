import base64
from datetime import datetime

import xlsxwriter
from six import BytesIO

from odoo import fields, models, api
from odoo.exceptions import UserError


class KgDealMilestone(models.Model):
    _name = 'kg.deal.milestone'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Activity'

    name = fields.Char()
    lead_id = fields.Many2one('crm.lead', string='Lead')
    activity_id = fields.Many2one('kg.activity', string='Activity')
    date = fields.Date('Date By')

    @api.model
    def create(self, vals):
        res = super(KgDealMilestone, self).create(vals)
        res.lead_id.update_step_no()
        return res

    def unlink(self):
        lead_id = self.lead_id
        res = super(KgDealMilestone, self).unlink()
        if lead_id:
            lead_id.update_step_no()
        return res
