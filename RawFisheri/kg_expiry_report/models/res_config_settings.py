# -*- coding: utf-8 -*-

from ast import literal_eval

from odoo import models, fields, api, _


class ResConfigSettings(models.TransientModel):
    """ Inherited to specify who all need to get notification for passport and seaman's book """
    _inherit = 'res.config.settings'

    passport_expiry_notification_employee_ids = fields.Many2many('hr.employee', 'passport_notif_rel_id',
                                                        string='Passport Expiry Notification')
    seamans_expiry_notification_employee_ids = fields.Many2many('hr.employee', 'seaman_notif_rel_id',
                                                       string="Seaman's Book Expiry Notification")

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('kg_expiry_report.passport_expiry_notification_employee_ids',
                                                         self.passport_expiry_notification_employee_ids.ids)
        self.env['ir.config_parameter'].sudo().set_param('kg_expiry_report.seamans_expiry_notification_employee_ids',
                                                         self.seamans_expiry_notification_employee_ids.ids)
        return res

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        with_user = self.env['ir.config_parameter'].sudo()
        passport_expiry = with_user.get_param('kg_expiry_report.passport_expiry_notification_employee_ids')
        seamans_expiry = with_user.get_param('kg_expiry_report.seamans_expiry_notification_employee_ids')

        res.update(passport_expiry_notification_employee_ids=[(6, 0, literal_eval(passport_expiry))] if passport_expiry else [],
                   seamans_expiry_notification_employee_ids=[(6, 0, literal_eval(seamans_expiry))] if seamans_expiry else [],
                   )
        return res
