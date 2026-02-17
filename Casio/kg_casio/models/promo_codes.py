# -*- coding: utf-8 -*-
# from odoo.exceptions import Warning

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import timedelta, date
import random
import string

class MassPromoMailing(models.Model):
    _name = 'mass.promo.mailing'

    def get_default_text(self):
        result = """
       <h3><span style="color: rgb(0, 0, 0); font-family: &quot;Times New Roman&quot;;">Hello ${object.partner_name},</span><br><br></h3><h3>Your Promo code is&nbsp;&nbsp;<span style="color: rgb(0, 0, 0); font-family: &quot;Times New Roman&quot;; font-style: inherit; font-variant-caps: inherit; font-variant-ligatures: inherit; font-weight: inherit; text-align: inherit;">&nbsp;${object.promo_code}</span></h3>"""
        return result
    name = fields.Char('Subject')
    date_sent = fields.Date('Date')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent')], string='Status', default='draft')
    cus_promo = fields.One2many('customer.promo.codes','mass_promo_id','Customer ')
    body_html = fields.Html('Body',default=get_default_text)

    promo_code_type = fields.Selection([('common','Common'),('random','Random')],string='Promo Code Type',default='common')
    promo_code_no = fields.Integer('Promo Code No',compute='comp_promo_code')
    mass_mailing_id = fields.Many2one('mailing.mailing','Mass Mailing')

    def comp_promo_code(self):
        for record in self:
            rec_count = self.env['customer.promo.codes'].search_count([('mass_promo_id','=',record.id)])
            record.promo_code_no = rec_count
    def action_view_mass_mailing(self):
        value = {
            'name': _('Mass Mailing'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mailing.mailing',
            'res_id': int(self.mass_mailing_id),

            'type': 'ir.actions.act_window',

        }
        return value


    def action_view_promo_codes(self):
        value = {
            'name': _('Promo Codes'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'customer.promo.codes',
            'domain': [('mass_promo_id', '=', self.id)],

            'type': 'ir.actions.act_window',

        }
        return value


    def set_promo_code(self):
        def get_random_alphaNumeric_string(stringLength=8):
            lettersAndDigits = string.ascii_uppercase + string.digits
            return ''.join((random.choice(lettersAndDigits) for i in range(stringLength)))
        for record in self:
            if record.promo_code_type == 'common':
                promo_code = get_random_alphaNumeric_string()
                for line in record.cus_promo:
                    line.promo_code = promo_code
            elif record.promo_code_type == 'random':
                for line in record.cus_promo:
                    rand_promo_code = get_random_alphaNumeric_string()
                    line.promo_code = rand_promo_code

    def reset_promo_code(self):
        for record in self:
            for line in record.cus_promo:
                line.promo_code = ''

    def sent_mail(self):
        mailing = self.env['mailing.mailing'].create({
            'name': self.name,
            'subject': self.name,

            'body_html': self.body_html,
            'reply_to_mode': 'email',

            'keep_archives': True,
             'mailing_model_id': self.env['ir.model']._get('customer.promo.codes').id,
             'mailing_domain': '%s' % [('mass_promo_id', 'in', self.ids),('blacklist','=',False)],


        })

        # mailing.action_put_in_queue()
        # mailing.action_send_mail()
        self.state='sent'
        self.mass_mailing_id = mailing.id



class CustomerPromoCodes(models.Model):
    _name = 'customer.promo.codes'
    _description = 'Customer Promo Codes'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']



    name  = fields.Char('Name')
    partner_id = fields.Many2one('res.partner','Customer')
    partner_name = fields.Char('Customer Name',required=True)
    email = fields.Char('Email',required=True)
    promo_code = fields.Char('Promo Code')
    mass_promo_id = fields.Many2one('mass.promo.mailing','Mass promo id')
    blacklist = fields.Boolean('BlackListed',default=False)

    @api.model
    def create(self,values):
        res = super(CustomerPromoCodes,self).create(values)
        if res.email:
            check_if_blacklisted = self.env['mail.blacklist'].search([('email','=',res.email)])
            if check_if_blacklisted:
                res.blacklist = True
            else:
                res.blacklist = False
        return res

    def write(self, vals):
        res = super(CustomerPromoCodes, self).write(vals)
        if vals.get('email'):
            check_if_blacklisted = self.env['mail.blacklist'].search([('email', '=', res.email)])
            if check_if_blacklisted:
                res.blacklist = True
            else:
                res.blacklist = False
        return res


    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            self.name = self.partner_id.name
            self.partner_name = self.partner_id.name
            self.email = self.partner_id.email
