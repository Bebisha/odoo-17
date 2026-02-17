# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import werkzeug

from odoo import http, _
from odoo.addons.phone_validation.tools import phone_validation
from odoo.http import request
from odoo.addons.mass_mailing_sms.controllers.main import MailingSMSController

class MailingSMSControllerInherit(MailingSMSController):



    @http.route(['/sms/<int:mailing_id>/unsubscribe/<string:trace_code>'], type='http', website=True, auth='public')
    def blacklist_number(self, mailing_id, trace_code, **post):
        check_res = self._check_trace(mailing_id, trace_code)
        if not check_res.get('trace'):
            return werkzeug.utils.redirect('/web')
        country_code = request.session.get('geoip', False) and request.session.geoip.get('country_code', False) if request.session.get('geoip') else None
        trace = check_res['trace']
        mailing_list_ids = trace.mass_mailing_id.contact_list_ids

        # parse and validate number
        sms_number = post.get('sms_number', '').strip(' ')
        sanitize_res = phone_validation.phone_sanitize_numbers([sms_number], country_code, None)[sms_number]
        tocheck_number = sanitize_res['sanitized'] or sms_number

        # compute opt-out / blacklist information
        lists_optout = request.env['mailing.list'].sudo()
        lists_optin = request.env['mailing.list'].sudo()
        unsubscribe_error = False
        if tocheck_number and trace.sms_number == tocheck_number:
            if mailing_list_ids:
                subscriptions = request.env['mailing.subscription'].sudo().search([
                    ('list_id', 'in', mailing_list_ids.ids),
                    ('contact_id.phone_sanitized', '=', tocheck_number),
                ])
                subscriptions.write({'opt_out': True})
                lists_optout = subscriptions.mapped('list_id')
            # else:
            blacklist_rec = request.env['phone.blacklist'].sudo().add(tocheck_number)
            print(blacklist_rec,'####################################??????')
            print(blacklist_rec,'####################################??????')
            print(blacklist_rec,'####################################??????')
            print(blacklist_rec,'####################################??????')
            blacklist_rec._message_log(
                body=_('Blacklist through SMS Marketing unsubscribe (mailing ID: %s - model: %s)') %
                      (trace.mass_mailing_id.id, trace.mass_mailing_id.mailing_model_id.display_name))
            lists_optin = request.env['mailing.subscription'].sudo().search([
                ('contact_id.phone_sanitized', '=', tocheck_number),
                ('list_id', 'not in', mailing_list_ids.ids),
                ('opt_out', '=', False),
            ]).mapped('list_id')
        elif tocheck_number and trace.sms_number != tocheck_number:
            unsubscribe_error = _('Number %s not found' % tocheck_number)
        else:
            unsubscribe_error = sanitize_res['msg']

        return request.render('mass_mailing_sms.blacklist_number', {
            'mailing_id': mailing_id,
            'trace_code': trace_code,
            'sms_number': sms_number,
            'lists_optin': lists_optin,
            'lists_optout': lists_optout,
            'unsubscribe_error': unsubscribe_error,
        })