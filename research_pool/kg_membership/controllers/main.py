# -*- encoding: utf-8 -*-
from datetime import datetime, timedelta, date

from odoo.addons.portal.controllers.portal import CustomerPortal, pager
from odoo import http
from odoo.http import request


class KGMembershipRegistrationPortal(CustomerPortal):

    @http.route('/portal/membership/registrations', type='http', auth='public', website=True)
    def membership_form(self, **kwargs):
        """Render the membership form."""
        countries = request.env['res.country'].search([])  # Fetch countries for the dropdown
        return request.render('kg_membership.membership_form_template', {
            'countries': countries
        })

    @http.route('/membership/submit', type='http', auth='public', methods=['POST'], website=True, csrf=True)
    def membership_submit(self, **post):
        """Handle the form submission."""
        # Extracting form data
        vals = {
            'name': post.get('name'),
            'email': post.get('email'),
            'phone': post.get('phone'),
            'street': post.get('street'),
            'city': post.get('city'),
            'zip': post.get('zip'),
            'country_id': int(post.get('country_id')) if post.get('country_id') else False,
            'membership_type': post.get('membership_type'),
            'associate_member': post.get('associate_member'),
        }

        membership = request.env['membership.model'].sudo().create(vals)


        return request.render('kg_membership.membership_success_template', {
            'membership': membership
        })
