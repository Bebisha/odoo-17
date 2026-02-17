# -*- encoding: utf-8 -*-
from odoo import models, fields, api
from datetime import date, timedelta, time, datetime
from odoo.exceptions import ValidationError

from odoo.exceptions import UserError


class KGEmulatorLicence(models.Model):
    _name = 'emulator.licence'
    _description = 'Emulator License Record'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="License Code")
    emulator_licence_type = fields.Selection([
        ('fx-9860GIII', "fx-9860GIII"),
        ('fx-82ZAPLUSII', "fx-82ZAPLUSII"),
        ('fx-991ZAPLUSII', "fx-991ZAPLUSII"),
    ], string="Emulator License Type")
    act_date = fields.Date(string="Activation Date")
    end_date = fields.Date(string="End Date")
    start_date = fields.Date(string="Start Date")
    allocated_teacher = fields.Char(string="Allocated Teacher")
    allocated_teachers = fields.Many2one('teacher.registration', string="Allocated Teacher")
    active = fields.Boolean(string='Active', default=True)
    allocated_date = fields.Date(string="Allocated date")
    is_new_allocated = fields.Boolean(string="New Allocated")
    is_first_register = fields.Boolean(string="First Allocation")
    state = fields.Selection([('new', 'New'), ('allocated', 'Allocated'), ('expire', 'Expired')], string='Status',
                             default='new')

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.start_date and record.end_date:
                if record.end_date <= record.start_date:
                    raise ValidationError("The End Date must be greater than the Start Date.")


    def send_low_stock_notification(self):
        conf_setting = []
        test = self.env['ir.config_parameter'].sudo().get_param('many2many.sending_facility')
        if test:
            conf_setting = list(map(int, test.split(',')))
        partners = self.env['res.partner'].search([('id', 'in', conf_setting)])
        license_types = ['fx-9860GIII', 'fx-82ZAPLUSII', 'fx-991ZAPLUSII']
        for license_type in license_types:
            active_license_count = self.env['emulator.licence'].search_count([
                ('active', '=', True),
                ('state', '=', 'new'),
                ('emulator_licence_type', '=', license_type)
            ])
            total_available_count = self.env['emulator.licence'].search_count([
                ('emulator_licence_type', '=', license_type),('state', '=', 'new')
            ])

            if active_license_count < 1000:
                if not partners:
                    return
                mail_content = (
                    "Dear Team,<br>"
                    "<br/>"
                    "This is to notify you that the number of remaining emulator licenses for type '{}' is below 1000.<br>"
                    "<br/>"
                    "Total Available Licenses: {}<br>"
                    "Please take necessary action.<br><br>"
                    "<br/>"
                    "Best Regards,<br>"
                    "CASIO Middle East and Africa Team"
                ).format(license_type, total_available_count)
                for partner in partners:
                    if partner.email:
                        email_values = {
                            'subject': 'Low Emulator Licenses Notification',
                            'body_html': mail_content,
                            'email_to': partner.email,
                        }
                        mail_mail = self.env['mail.mail'].sudo().create(email_values)
                        mail_mail.send()
                    else:
                        raise UserError(f"The partner {partner.name} does not have an email address.")

    # @api.model
    # def send_expiry_notifications(self):
    #     notification_date = date.today() + timedelta(days=15)
    #
    #
    #     expiring_licenses = self.env['emulator.licence'].search(
    #         [('end_date', '=', notification_date), ('is_new_allocated', '=', False),('is_first_register','=',True),
    #          ('state', '!=', 'expire')]
    #     )
    #     if not expiring_licenses:
    #         return
    #     url_mapping = {
    #         'fx-9860GIII': 'https://edu.casio.com/freetrial/en/freetrial_form.php?dl_FILE_NO=20374&LANGUAGE=1',
    #         'fx-82ZAPLUSII': 'https://edu.casio.com/freetrial/en/freetrial_form.php?dl_FILE_NO=20146&LANGUAGE=1',
    #         'fx-991ZAPLUSII': 'https://edu.casio.com/freetrial/en/freetrial_form.php?dl_FILE_NO=20147&LANGUAGE=1',
    #     }
    #
    #     for license in expiring_licenses:
    #         teacher = license.allocated_teachers
    #         if teacher:
    #             active_licenses = self.search(
    #                 [('emulator_licence_type', '=', license.emulator_licence_type), ('active', '=', True),('state','=','new')]
    #             )
    #             license.state = 'expire'
    #
    #             if active_licenses:
    #                 first_active_license = active_licenses[0]
    #                 new_license_code = first_active_license.name
    #                 download_url = url_mapping.get(license.emulator_licence_type)
    #                 mail_content = (
    #                     f"Dear {teacher.name},<br>"
    #                     "<br/>"
    #                     f"Your emulator license code <strong>{license.name}</strong> will expire soon.<br><br>"
    #                     "Please find the emulator license code below:<br>"
    #                     "<br/>"
    #                     f"Model Name: {teacher.emulator_licence_type}<br>"
    #                     f"New Licence Code: {new_license_code}<br>"
    #                     f"Activation Date: {first_active_license.act_date.strftime('%Y-%m-%d')}<br><br>"
    #                     "<br/>"
    #                     "To use the emulator on your PC, you need to download the emulator software from the URL below:<br>"
    #                      f"<a href='{download_url}' target='_blank'>{download_url}</a><br>"                "<br>"
    #                     "Sincerely,<br>"
    #                     "CASIO Middle East and Africa Team"
    #                 )
    #                 subject = 'Emulator License Expiry Notification'
    #                 email_values = {
    #                     'subject': subject,
    #                     'body_html': mail_content,
    #                     'email_to': teacher.email,
    #                 }
    #                 mail_mail = self.env['mail.mail'].sudo().create(email_values)
    #                 mail_mail.send()
    #                 license.message_post(body=f"License {license.name} is expiring. Notified teacher {teacher.name}.")
    #                 teacher.sudo().write(
    #                     {'emulator_licence': new_license_code, 'emul_licence_id': first_active_license.id}
    #                 )
    #                 teacher.message_post(
    #                     body=f"emulator_licence {new_license_code} is updated. Notified teacher {teacher.name}."
    #                 )
    #                 first_active_license.sudo().write(
    #                     {'is_first_register':True, 'is_new_allocated': True, 'allocated_teacher': teacher.name,
    #                      'allocated_teachers': teacher.id, 'state': 'allocated'}
    #                 )
    #                 first_active_license.message_post(
    #                     body=f"License {first_active_license.name} allocated to {teacher.name}."
    #                 )
    #
    #             else:
    #                 license.state = 'allocated'
    #                 license.message_post(body="No license found for the same emulator license type in the List.")
    #                 conf_setting = []
    #                 test = self.env['ir.config_parameter'].sudo().get_param('many2many.sending_facility')
    #                 if test:
    #                     conf_setting = list(map(int, test.split(',')))
    #                 partners = self.env['res.partner'].search([('id', 'in', conf_setting)])
    #                 if not active_licenses:
    #                     if not partners:
    #                         return
    #                     mail_content = (
    #                         f"Dear Team,<br>"
    #                          "<br/>"
    #                         f"No active license is available for the emulator license type: <strong>{license.emulator_licence_type}</strong>.<br>"
    #                         f"Please take the necessary actions to allocate new licenses.<br><br>"
    #                         "Best regards,<br>"
    #                         "CASIO Middle East and Africa Team"
    #                     )
    #                     for partner in partners:
    #                         if partner.email:
    #                             email_values = {
    #                                 'subject': f'No Active Emulator Licenses for {license.emulator_licence_type}',
    #                                 'body_html': mail_content,
    #                                 'email_to': partner.email,
    #                             }
    #                             mail_mail = self.env['mail.mail'].sudo().create(email_values)
    #                             mail_mail.send()


