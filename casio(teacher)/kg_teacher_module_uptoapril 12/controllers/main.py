# -*- encoding: utf-8 -*-
from datetime import datetime, timedelta, date


from odoo.addons.portal.controllers.portal import CustomerPortal, pager
import requests

from odoo import http
from odoo.http import request,_logger
import re
import json
from urllib.request import urlopen



class TeacherRegistrationPortal(CustomerPortal):

    @http.route('/', type='http', auth='public', website=True)
    def home_redirect(self, **kwargs):
       return request.redirect('/web/login')

    @http.route('/portal/contact_us', type='http', auth='public', website=True)
    def contact_form(self, **kwargs):
        return request.redirect('https://casio-mea.com/contact')

    @http.route('/portal/registration_form/thank_you', type='http', auth='public', website=True)
    def submit_registration(self, **kwargs):
        return request.render('kg_teacher_module.registration_portal_thanks')

    @http.route('/portal/teacher_license_code', type='http', auth='public', website=True)
    def registration_form(self, **kwargs):
        client_ip = request.httprequest.remote_addr
        _logger.info(f"Client IP: {client_ip}")

        url = f"https://ipinfo.io/{client_ip}/json"
        response = requests.get(url)
        data = response.json()
        _logger.info(f"IP Info Data: {data}")

        country = data.get('country', 'Unknown')
        _logger.info(f"Client Country: {country}")
        allowed_countries = ['ZA', 'NG', 'KE', 'EG', 'GH', 'MA']
        # allowed_countries = [
        #     'DZ', 'AO', 'BJ', 'BW', 'BF', 'BI', 'CM', 'CV', 'CF', 'TD', 'KM', 'CG', 'CD', 'CI',
        #     'DJ', 'EG', 'GQ', 'ER', 'SZ', 'ET', 'GA', 'GM', 'GH', 'GN', 'GW', 'KE', 'LS', 'LR',
        #     'LY', 'MG', 'MW', 'ML', 'MR', 'MU', 'YT', 'MA', 'MZ', 'NA', 'NE', 'NG', 'RW', 'RE',
        #     'SH', 'ST', 'SN', 'SC', 'SL', 'SO', 'ZA', 'SS', 'SD', 'TZ', 'TG', 'TN', 'UG', 'EH',
        #     'ZM', 'ZW'
        # ]
        if country not in allowed_countries:
            return request.redirect('/web/login')
        emulator_licences = request.env['emulator.licence'].sudo().search(
            [('active', '=', True), ('state', '=', 'new')])
        return request.render('kg_teacher_module.portal_registration_form', {
            'emulator_licences': emulator_licences,
        })

    @http.route('/portal/registration/submit', type='http', auth='public', methods=['POST'], website=True, csrf=False)
    def submit_registration_form(self, **post):
        name = post.get('name')
        name_of_school = post.get('name_of_school')
        email = post.get('email')
        emulator_licence_id = post.get('emulator_licence')
        email = email.lower().strip()
        existing_registration = request.env['teacher.registration'].sudo().search([
            ('email', '=', email),
            ('emulator_licence_type', '=', emulator_licence_id)
        ], limit=1)
        if existing_registration:
            error_message = "You have already registered with this license type using this email address."
            emulator_licences = request.env['emulator.licence'].sudo().search(
                [('active', '=', True), ('state', '=', 'new')])
            emulator_licence_types = emulator_licences.mapped('emulator_licence_type')

            return request.render('kg_teacher_module.portal_registration_form', {
                'emulator_licences': emulator_licences,
                'emulator_licence_types': emulator_licence_types,
                'error_message_mail': error_message,
                'email': email,
            })
        emulator_licences = request.env['emulator.licence'].sudo().search([('state', '=', 'new')])
        matching_licences = emulator_licences.filtered(lambda l: l.emulator_licence_type == emulator_licence_id)

        url_mapping = {
            'fx-9860GIII': 'https://edu.casio.com/freetrial/en/freetrial_form.php?dl_FILE_NO=20374&LANGUAGE=1',
            'fx-82ZAPLUSII': 'https://edu.casio.com/freetrial/en/freetrial_form.php?dl_FILE_NO=20146&LANGUAGE=1',
            'fx-991ZAPLUSII': 'https://edu.casio.com/freetrial/en/freetrial_form.php?dl_FILE_NO=20147&LANGUAGE=1',

        }
        if matching_licences:
            first_matching_licence = matching_licences[0]
            first_matching_licence_id = first_matching_licence.id
            registration = request.env['teacher.registration'].sudo().create({
                'name': name,
                'email': email,
                'name_of_school': name_of_school,
                'emulator_licence_type': emulator_licence_id,
                'emulator_licence': first_matching_licence.name,
                'emul_licence_id': first_matching_licence_id,
                'end_date_emulator_licence': date.today(),

            })
            registration.message_post(body=f"License {first_matching_licence.name} allocated to {name}.")
            first_matching_licence.sudo().write({
                'is_first_register': True,
                # 'is_new_allocated': True,
                'allocated_teacher': name,
                'allocated_date': date.today(),
                'act_date': date.today(),
                'allocated_teachers': registration.id,
                'state': 'allocated'
            })
            download_url = url_mapping.get(emulator_licence_id)
            mail_content = (
                f"Dear {name},<br>"
                "<br/>"
                "Your Emulator License Code is ready to be activated, details are below,<br>"
                "<br/>"
                f"Model Name: {emulator_licence_id}<br>"
                f"License Code: {first_matching_licence.name}.<br><br>"
                "To use the emulator on your PC, you need to download the emulator software from the URL below:<br>"
                f"<a href='{download_url}' target='_blank'>{download_url}</a><br>"                "<br>"
                "Sincerely,<br>"
                "CASIO Middle East and Africa Team"
            )

            email_values = {
                'subject': 'Registration Notification',
                'body_html': mail_content,
                'email_to': email,
            }

            mail_mail = request.env['mail.mail'].sudo().create(email_values)
            mail_mail.send()

            first_matching_licence.message_post(body=f"Licence {first_matching_licence.name} allocated to {name}.")

            return request.redirect('/portal/registration_form/thank_you?name=%s&email=%s' %
                                    (name, email))

        else:
            error_message = "The provided Emulator license type is not valid."
            emulator_licences = request.env['emulator.licence'].sudo().search(
                [('active', '=', True), ('state', '=', 'new')])
            emulator_licence_types = request.env['emulator.licence'].sudo().search([ ('state', '=', 'new')]).mapped('emulator_licence_type')

            return request.render('kg_teacher_module.portal_registration_form', {
                'emulator_licences': emulator_licences,
                'emulator_licence_types': emulator_licence_types,
                'error_message': error_message,
            })

    @http.route(['/terms/conditions'], type='http', auth='public', website=True)
    def template_terms(self, **kwargs):
        return request.render('kg_teacher_module.terms_condition_template')
