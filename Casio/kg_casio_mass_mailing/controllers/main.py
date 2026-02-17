# Part of Odoo. See LICENSE file for full copyright and licensing details.
import base64

import werkzeug
from werkzeug.exceptions import NotFound, Unauthorized

from odoo import _, exceptions, http, tools
from odoo.http import request
from odoo.tools import consteq
from odoo.addons.mass_mailing.controllers.main import MassMailController


class MassMailControllerInh(MassMailController):

    @http.route('/mailing/my', type='http', website=True, auth='user')
    def mailing_my(self):
        """This function is overrided to redirect to the custom form """
        email, _hash_token = self._fetch_user_information(None, None)
        if not email:
            raise Unauthorized()
        render_values = self._prepare_mailing_subscription_values(
            request.env['mailing.mailing'], False, email, None
        )
        render_values.update(feedback_enabled=False)
        frequency = request.env['email.preferences'].sudo().search([])
        reasons = request.env['unsubscribe.reason'].sudo().search([])
        return request.render('kg_casio_mass_mailing.unsubscribe_reason_template', {
            'reasons': reasons,
            'frequency': frequency,
            'email': email,
            'mailing_id': False,
            'res_id': False,
            # 'list_ids': opt_in_lists,
            'show_blacklist_button': request.env['ir.config_parameter'].sudo().get_param(
                'mass_mailing.show_blacklist_buttons'),
        })
        return request.redirect('/web')
        # return request.render(
        #     'mass_mailing.page_mailing_unsubscribe',
        #     render_values
        # )


    @http.route(['/mailing/<int:mailing_id>/unsubscribe'], type='http', website=True, auth='public')
    def mailing_unsubscribe(self, mailing_id, document_id=None, email=None, hash_token=None):

        email_found, hash_token_found = self._fetch_user_information(email, hash_token)
        mailing = request.env['mailing.mailing'].sudo().browse(mailing_id)
        #

        if mailing.exists():
            if mailing.mailing_model_real == 'mailing.contact':
                try:
                    mailing_sudo = self._check_mailing_email_token(
                        mailing_id, document_id, email_found, hash_token_found,
                        required_mailing_id=True
                    )
                    print(mailing_sudo, 'ssssssss')

                except NotFound as e:  # avoid leaking ID existence
                    raise Unauthorized() from e

                if mailing_sudo.mailing_on_mailing_list:
                    return self._mailing_unsubscribe_from_list(mailing_sudo, document_id, email_found, hash_token_found)
                return self._mailing_unsubscribe_from_document(mailing_sudo, document_id, email_found, hash_token_found)
            else:
                frequency = request.env['email.preferences'].sudo().search([])
                reasons = request.env['unsubscribe.reason'].sudo().search([])
                return request.render('kg_casio_mass_mailing.unsubscribe_reason_template', {
                    'reasons': reasons,
                    'frequency': frequency,
                    'email': email,
                    'mailing_id': mailing_id,
                    'res_id': document_id,
                    # 'list_ids': opt_in_lists,
                    'show_blacklist_button': request.env['ir.config_parameter'].sudo().get_param(
                        'mass_mailing.show_blacklist_buttons'),
                })
                return request.redirect('/web')

    # @http.route(['/mail/mailing/<int:mailing_id>/unsubscribe'], type='http', website=True, auth='public')
    # def mailing(self, mailing_id, email=None, res_id=None, token="", **post):
    #     print('hhhhhhhhhhh')
    #     mailing = request.env['mailing.mailing'].sudo().browse(mailing_id)
    #
    #     if mailing.exists():
    #         res_id = res_id and int(res_id)
    #         # uncomment on commit
    #         # if not self._valid_unsubscribe_token(mailing_id, res_id, email, str(token)):
    #         #     raise exceptions.AccessDenied()
    #
    #         if mailing.mailing_model_real == 'mailing.contact':
    #             # Unsubscribe directly + Let the user choose his subscriptions
    #             mailing.update_opt_out(email, mailing.contact_list_ids.ids, True)
    #
    #             contacts = request.env['mailing.contact'].sudo().search(
    #                 [('email_normalized', '=', tools.email_normalize(email))])
    #             subscription_list_ids = contacts.mapped('subscription_list_ids')
    #             # In many user are found : if user is opt_out on the list with contact_id 1 but not with contact_id 2,
    #             # assume that the user is not opt_out on both
    #             # TODO DBE Fixme : Optimise the following to get real opt_out and opt_in
    #             opt_out_list_ids = subscription_list_ids.filtered(lambda rel: rel.opt_out).mapped('list_id')
    #             opt_in_list_ids = subscription_list_ids.filtered(lambda rel: not rel.opt_out).mapped('list_id')
    #             opt_out_list_ids = set([list.id for list in opt_out_list_ids if list not in opt_in_list_ids])
    #
    #             unique_list_ids = set([list.list_id.id for list in subscription_list_ids])
    #             list_ids = request.env['mailing.list'].sudo().browse(unique_list_ids)
    #             unsubscribed_list = ', '.join(str(list.name) for list in mailing.contact_list_ids if list.is_public)
    #             return request.render('mass_mailing.page_mailing_unsubscribe', {
    #                 'contacts': contacts,
    #                 'list_ids': list_ids,
    #                 'opt_out_list_ids': opt_out_list_ids,
    #                 'unsubscribed_list': unsubscribed_list,
    #                 'email': email,
    #                 'mailing_id': mailing_id,
    #                 'res_id': res_id,
    #                 'show_blacklist_button': request.env['ir.config_parameter'].sudo().get_param(
    #                     'mass_mailing.show_blacklist_buttons'),
    #             })
    #         else:
    #             frequency = request.env['email.preferences'].sudo().search([])
    #             reasons = request.env['unsubscribe.reason'].sudo().search([])
    #             return request.render('kg_casio_mass_mailing.unsubscribe_reason_template', {
    #                 'reasons': reasons,
    #                 'frequency': frequency,
    #                 'email': email,
    #                 'mailing_id': mailing_id,
    #                 'res_id': res_id,
    #                 # 'list_ids': opt_in_lists,
    #                 'show_blacklist_button': request.env['ir.config_parameter'].sudo().get_param(
    #                     'mass_mailing.show_blacklist_buttons'),
    #             })
    #     return request.redirect('/web')

    @http.route('/mass_mail/unsubscribe/submit', type='http', auth='public', website=True)
    def mass_mail_unsubscribe_submit(self, **post):
        print("post.get('b_type')---->",post.get('b_type'))
        print("email---->", post.get('email'))
        if post.get('b_type') == "value":
            partner_id = request.env.user.partner_id.id
            partner = request.env['res.partner'].sudo().browse(partner_id)
            pre = http.request.env['email.preference'].sudo().create({
                'name': post.get('name'),
                'email': post.get('email'),
                'reason': post.get('reason'),
                'frequency': post.get('frequency'),
                'other_reason': post.get('unsubscribe_other_reason')
            })
            print("pre------->",pre)
            return request.render('kg_casio_mass_mailing.unsubscribe_confirmation_template')
        else:
            email = post.get('email')
            mailing_id = post.get('mailing_id')
            opt_in_lists = request.env['mailing.subscription'].sudo().search([
                ('contact_id.email_normalized', '=', email),
                ('opt_out', '=', False)
            ]).mapped('list_id')
            blacklist_rec = request.env['mail.blacklist'].sudo()._add(email)
            blacklist_rec.update({'reason': int(post.get('reason')), 'other_reason': post.get('unsubscribe_other_reason')})
            # pre = http.request.env['unsubscribe.reasons'].sudo().create({
            #     'email': post.get('email'),
            #     'reason': post.get('reason'),
            #     'other_reason': post.get('unsubscribe_other_reason')
            # })
            # print("pre---->>",pre)
            # self._log_blacklist_action(
            #     blacklist_rec, mailing_id,
            #     _("""Requested blacklisting via unsubscribe link."""))
            return request.render('kg_casio_mass_mailing.page_unsubscribed', {
                'email': email,
                'mailing_id': mailing_id,
                # 'res_id': res_id,
                'list_ids': opt_in_lists,
                'show_blacklist_button': request.env['ir.config_parameter'].sudo().get_param(
                    'mass_mailing.show_blacklist_buttons'),
            })

