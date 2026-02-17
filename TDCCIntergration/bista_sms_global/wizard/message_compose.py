# -*- encoding: utf-8 -*-
#
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
#
import warnings

from odoo import api, fields, models,_


class MessageCompose(models.TransientModel):
    _name = 'message.compose'
    _description = "Compose Message"

    @api.model
    def default_get(self, fields):
        context = dict(self._context)
        res = super(MessageCompose, self).default_get(fields)
        sms_server_id = self.env['ir.sms_server'].search(
            [], order='sequence', limit=1)
        res.update(
            {'sms_server_id': sms_server_id and sms_server_id.id or False,
             'from_number': sms_server_id and sms_server_id.from_no,
             'model': context.get('active_model')})
        default_sms_template_id = self.env['sms.template'].search(
            [('model', '=', context.get('active_model'))], limit=1)
        if default_sms_template_id:
            res.update({'sms_template_id': default_sms_template_id.id})
        return res

    from_number = fields.Char(string='From', required=True)
    to_number = fields.Char(string='To', required=True)
    reply_to = fields.Char(string='Reply To')
    model = fields.Char(string='Model')
    sms_template_id = fields.Many2one('sms.template', string='Use template')
    message = fields.Text(string='Message')
    sms_server_id = fields.Many2one('ir.sms_server', string='Server')

    @api.onchange('sms_template_id')
    def onchange_template_id(self):
        sms_tmpl_obj = self.env['sms.template']
        res_ids = self._context.get('active_ids')
        for res_id in res_ids:
            if self.sms_template_id:
                self.model = self.sms_template_id.model_id.model
                self.from_number = self.sms_template_id.from_number
                self.to_number = self.sms_template_id.to_number
                self.message = self.sms_template_id.message

    # @api.multi
    def send_message(self):
        message_obj = self.env['message.message']
        active_model = self._context['active_model']
        sms_tmpl_obj = self.env['sms.template']

        for res_id in self.env[active_model].browse(self._context['active_ids']):
            if active_model == 'appointment.appointment':
                if res_id.state == 'new':
                    continue  # Ensure this continues properly
                partner_id = res_id.client_id
            else:
                partner_id = res_id

            to_number = sms_tmpl_obj._render_template(
                self.to_number, self.model, res_id.ids)
            message = sms_tmpl_obj._render_template(
                self.message, self.model, res_id.ids)

            message_vals = {
                'from_number': self.from_number,
                'model': active_model or self.model,
                'name': self.sms_template_id.name,
                'res_id': res_id.id,
                'partner_ids': [(6, 0, partner_id.ids)],
                'to_number': to_number[res_id.id],
                'sms_template_id': self.sms_template_id.id or False,
                'reply_to': self.reply_to or '',
                'message': message[res_id.id],
                'sms_server_id': self.sms_server_id.id or False
            }

            message_obj.create(message_vals)

        return True
