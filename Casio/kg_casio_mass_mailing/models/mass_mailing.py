from odoo import api, fields, models
from ast import literal_eval
from dateutil.relativedelta import relativedelta


class MassMail(models.Model):
    _inherit = 'mailing.mailing'

    def get_mail_list(self):
        partners_model = self.env[self.mailing_model_real].browse(self._get_recipients())
        obj_list = []
        if self.mailing_model_real == 'customer.promo.codes':
            for rec in partners_model:
                pref = self.env['email.preference'].search([('email','=',rec.email)],limit=1,order='id desc')
                frq = 0
                if len(pref) != 0:
                    digit = [int(s) for s in pref.frequency.name.split() if s.isdigit()]
                    if len(digit) != 0:
                        frq = int(digit[0])
                sent = self.env['mailing.trace'].search_count(
                    [('email', '=', rec.email), ('trace_status', 'not in', ['exception', 'bounced']),
                     ('sent_datetime', '>=', fields.Datetime.now() - relativedelta(days=30))])
                blk_list = self.env['mail.blacklist'].search([('email', '=', rec.email)], limit=1, order='id desc')
                is_remove = False
                if len(blk_list) != 0 or (frq <= sent and frq != 0):
                    is_remove = True
                obj_list.append((0, 0,{'object_id':rec.id,'partner_id':rec.partner_id.id,'email':rec.email,'preference':pref.frequency.id.id if len(pref)!=0 else False,'fully_unsubscribed':'Yes' if len(blk_list)!= 0 else 'No','is_removed':is_remove,'total_email_sent':sent }))
        elif self.mailing_model_real == 'res.partner':
            for rec in partners_model:
                pref = self.env['email.preference'].search([('email', '=', rec.email)], limit=1, order='id desc')
                frq = 0
                if len(pref)!= 0:
                    digit = [int(s) for s in pref.frequency.name.split() if s.isdigit()]
                    if len(digit)  != 0:
                        frq = int(digit[0])
                sent = self.env['mailing.trace'].search_count([('email','=',rec.email),('trace_status', 'not in',['exception','bounced']),('sent_datetime','>=',fields.Datetime.now() - relativedelta(days=30))])
                blk_list = self.env['mail.blacklist'].search([('email', '=', rec.email)], limit=1, order='id desc')
                is_remove = False
                if len(blk_list) != 0 or (frq <= sent and frq != 0):
                    is_remove = True
                obj_list.append((0, 0,{'object_id':rec.id,'partner_id': rec.id, 'email': rec.email,'preference':pref.frequency.id if len(pref)!=0 else False,'fully_unsubscribed':'Yes' if len(blk_list)!= 0 else 'No','is_removed':is_remove,'total_email_sent':sent}))
        elif self.mailing_model_real == 'crm.lead':
            for rec in partners_model:
                pref = self.env['email.preference'].search([('email', '=', rec.email_from)], limit=1, order='id desc')
                frq = 0
                if len(pref) != 0:
                    digit = [int(s) for s in pref.frequency.name.split() if s.isdigit()]
                    if len(digit) != 0:
                        frq = int(digit[0])
                sent = self.env['mailing.trace'].search_count(
                    [('email', '=', rec.email_from), ('trace_status', 'not in', ['exception', 'bounced']),
                     ('sent_datetime', '>=', fields.Datetime.now() - relativedelta(days=30))])
                blk_list = self.env['mail.blacklist'].search([('email', '=', rec.email_from)], limit=1, order='id desc')
                is_remove = False
                if len(blk_list) != 0 or (frq <= sent and frq != 0):
                    is_remove = True
                obj_list.append((0, 0,{'object_id':rec.id,'partner_id': rec.partner_id.id, 'email': rec.email_from,'preference':pref.frequency.id if len(pref)!=0 else False,'fully_unsubscribed':'Yes' if len(blk_list)!= 0 else 'No','is_removed':is_remove,'total_email_sent':sent}))
        elif self.mailing_model_real == 'mailing.contact':
            for rec in partners_model:
                pref = self.env['email.preference'].search([('email', '=', rec.email)], limit=1, order='id desc')
                frq = 0
                if len(pref) != 0:
                    digit = [int(s) for s in pref.frequency.name.split() if s.isdigit()]
                    if len(digit) != 0:
                        frq = int(digit[0])
                sent = self.env['mailing.trace'].search_count([('email','=',rec.email),('trace_status', 'not in',['exception','bounced']),('sent_datetime','>=',fields.Datetime.now() - relativedelta(days=30))])
                blk_list = self.env['mail.blacklist'].search([('email', '=', rec.email)], limit=1, order='id desc')
                is_remove = False
                if len(blk_list) != 0 or (frq <= sent and frq != 0):
                    is_remove = True
                obj_list.append((0, 0,{'object_id':rec.id,'email': rec.email,'preference':pref.frequency.id if len(pref)!=0 else False,'fully_unsubscribed':'Yes' if len(blk_list)!= 0 else 'No','is_removed':is_remove,'total_email_sent':sent}))
        list = self.env['email.list'].create({})
        list.line_ids = obj_list
        [action] = self.env.ref('kg_casio_mass_mailing.email_list_action').read()
        action['res_id'] = list.id
        return action
