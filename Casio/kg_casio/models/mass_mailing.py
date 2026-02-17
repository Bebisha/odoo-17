# -*- coding: utf-8 -*-

from odoo import _, api, fields, models, modules, tools

MASS_MAILING_BUSINESS_MODELS_IMP = [
    'crm.lead',
    'event.registration',
    'hr.applicant',
    'res.partner',
    'event.track',
    'sale.order',
    'mailing.list',
    'mailing.contact',
    'customer.promo.codes'
]


class MassMailing(models.Model):
    _inherit = 'mailing.mailing'

    @api.model
    def get_default_from(self):
        if self.env.user.company_id.email:
            return tools.formataddr(('G-SHOCK Club', self.env.user.company_id.email))
        else:
            return tools.formataddr(('G-SHOCK Club', 'gclub@casiomea.com'))

    select_from_email = fields.Many2one('email.from.address', 'From Email List')

    @api.onchange('select_from_email')
    def onchange_select_from_email(self):
        for record in self:
            if record.select_from_email:
                record.email_from = tools.formataddr((record.select_from_email.name, record.select_from_email.email))
                record.select_from_email = None

    mailing_model_id = fields.Many2one('ir.model', string='Recipients Model',
                                       domain=[('model', 'in', MASS_MAILING_BUSINESS_MODELS_IMP)],
                                       default=lambda self: self.env.ref('mass_mailing.model_mailing_list').id)
    email_from = fields.Char(string='Send From', required=True,
                             default=get_default_from)

    reply_to = fields.Char(string='Reply To', help='Preferred Reply-To Address',
                           default=get_default_from)
