from odoo import models, fields,_

class UnsubscribeReason(models.Model):
    _name = 'unsubscribe.reason'
    _description = 'Unsubscribe Reasons'

    name = fields.Char(string='Reason', required=True)
    is_other = fields.Boolean(string='Other')


class ResPartner(models.Model):
    _inherit = 'res.partner'

    masg_count = fields.Integer(compute='get_msg_count')

    def show_customer_preference(self):
        preference = self.env['email.preference'].sudo().search([('email','=',self.email)])
        [action] = self.env.ref('kg_casio_mass_mailing.mail_preference_action').read()
        action['domain'] = [('id', 'in', preference.ids)]
        return action

    def show_unsub_reason(self):
        reason = self.env['mail.blacklist'].sudo().search([('email','=',self.email)])
        [action] = self.env.ref('mail.mail_blacklist_action').read()
        action['domain'] = [('id', 'in', reason.ids)]
        return action

    def show_survay_details(self):
        answer = self.env['survey.user_input'].sudo().search([('email','=',self.email)])
        [action] = self.env.ref('survey.action_survey_user_input').read()
        action['domain'] = [('id', 'in', answer.ids)]
        return action

    def get_msg_count(self):
        for rec in self:
            rec.masg_count = len(self.env['survey.user_input'].sudo().search([('email','=',self.email)]))



class Blacklist (models.Model):
    _inherit = 'mail.blacklist'

    reason = fields.Many2one('unsubscribe.reason', string='Reason')
    other_reason = fields.Char()