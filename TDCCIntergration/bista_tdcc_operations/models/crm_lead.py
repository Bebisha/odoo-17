# -*- encoding: utf-8 -*-
#
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
#

from odoo import models, fields, api


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    service_group_id = fields.Many2one('service.group', string="Service Group")
    service_type_id = fields.Many2one('service.type', string="Service Type")
    program_type = fields.Selection(related='team_id.program_type',
                                    string="Program Type")
    parent_name = fields.Char(string='Father Name')
    mother_name = fields.Char(string='Mother Name')
    client_last_name = fields.Char(string='Client Last Name')
    dob = fields.Date(string='Birthdate')
    school_id = fields.Many2one('school.school', string='School ')
    gender = fields.Selection([('male', 'Male'),
                               ('female', 'Female')],
                              string="Gender")
    app_medium_id = fields.Many2one('appointment.medium', string='Appointment Medium')


    def print_eiip_registration_form(self):
        return self.env.ref('bista_tdcc_operations.'
                            'action_eiip_registration_form'
                            ).report_action(self)


    def _create_lead_partner_data(self, name, is_company, parent_id=False):
        res = super(CrmLead, self)._create_lead_partner_data(name, False)
        # Mark is Student True and Update student information
        res.update({
            'is_student': True,
            'dob': self.dob or False,
            'medium_id': self.app_medium_id.id or False,
            'gender': self.gender or False,
            'school_id': self.school_id.id or False,
            'father_name': self.parent_name or False,
            'mother_name' : self.mother_name or False
        })
        # Update Student first name and last name
        if self.contact_name and self.client_last_name:
            res.update({
                'name': self.contact_name + " " + self.client_last_name,
                'first_name': self.contact_name,
                'last_name': self.client_last_name
            })
        elif self.contact_name and not self.client_last_name:
            res.update({
                'first_name': self.contact_name,
                'name': self.contact_name
            })
        elif self.client_last_name and not self.contact_name:
            res.update({
                'last_name': self.client_last_name,
                'name': self.client_last_name
            })
        return res

#     @api.multi
#     def message_post(self, body='', subject=None,
#                      message_type='notification', subtype=None,
#                      parent_id=False, attachments=None,
#                      notif_layout=False, add_sign=True, model_description=False,
#                      mail_auto_delete=True, **kwargs):
#         return super(CrmLead, self).message_post(body='', subject=None,
#                      message_type='comment', subtype=None,
#                      parent_id=False, attachments=None,
#                      notif_layout=False, add_sign=True, model_description=False,
#                      mail_auto_delete=True, **kwargs)

    @api.onchange('user_id')
    def onchange_user_id(self):
        if not self.user_id:
            self.team_id == False
        else:
            self.team_id = self.user_id.sale_team_id.id


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    program_type = fields.Selection([('360', '360'), ('eip', 'EIP'),
                                     ('eiip', ' Intensive Program')],
                                    string="Program Type")
