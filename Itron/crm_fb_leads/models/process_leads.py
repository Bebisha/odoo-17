# -*- coding: utf-8 -*-
# Copyright 2020 - Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
import logging
import requests

from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class CRMFacebookLead(models.Model):
    _inherit = 'crm.lead'

    fb_lead_id = fields.Char(readonly=True)
    lead_form_id = fields.Many2one('fb.lead.form', readonly=True)
    fb_page_id = fields.Many2one('fb.page', store=True, readonly=True)

    @api.model
    def create(self, vals):
        if vals.get('contact_name'):
            vals['name'] = vals['contact_name'] + " - " + vals['name']

        if vals.get('lead_form_id'):
            lead_form = self.env['fb.lead.form'].sudo().browse(vals['lead_form_id'])
            print(lead_form,'lead_form')
            if lead_form and lead_form.lead_interest_id:
                vals['lead_interest_id'] = lead_form.lead_interest_id.id

        res = super(CRMFacebookLead, self).create(vals)
        return res

    @api.model
    def get_all_facebook_leads(self):
        medium_id = self.env['utm.medium'].search([('name', '=', 'Facebook')], limit=1)
        source_id = self.env['utm.source'].search([('name', '=', 'Facebook')], limit=1)

        for page in self.env['fb.page'].search([]):
            lead_forms = self.env['fb.lead.form'].search([('fb_page_id', '=', page.id)])
            # /!\ NOTE: Load forms
            for form in lead_forms:
                if form.fb_page_id and form.fb_page_id.page_access_token:
                    resp = requests.get("https://graph.facebook.com/v15.0/" + form.form_id + "/leads",
                                        params={'access_token': form.fb_page_id.page_access_token,
                                                'fields': 'created_time,field_data,is_organic'}).json()
                    # /!\ NOTE: Checking Response
                    if not resp.get('data'):
                        continue
                    for data in resp['data']:
                        # /!\ NOTE: Cleaning data
                        field_data = data.pop('field_data')
                        lead_data = dict(data)
                        lead_data.update([(l['name'], l['values'][0])
                                          for l in field_data
                                          if l.get('name') and l.get('values')])
                        lead = lead_data
                        # /!\ NOTE: Fields mapping
                        if not self.search([('fb_lead_id', '=', lead.get('id')), '|', ('active', '=', True),
                                            ('active', '=', False)]):
                            vals, notes = {}, []
                            field_mapping = form.map_ids.filtered(lambda m: m.odoo_field).mapped('lead_field')
                            unmapped_fields = []
                            for name, value in lead.items():
                                if name not in field_mapping:
                                    unmapped_fields.append((name, value))
                                    continue
                                odoo_field = form.map_ids.filtered(lambda m: m.lead_field == name).odoo_field
                                notes.append('%s: %s' % (odoo_field.field_description, value))
                                if odoo_field.ttype == 'many2one':
                                    related_value = self.env[odoo_field.relation].search(
                                        [('display_name', '=', value)])
                                    vals.update({odoo_field.name: related_value and related_value.id})
                                elif odoo_field.ttype in ('float', 'monetary'):
                                    vals.update({odoo_field.name: float(value)})
                                elif odoo_field.ttype == 'integer':
                                    vals.update({odoo_field.name: int(value)})
                                elif odoo_field.ttype in ('date', 'datetime'):
                                    vals.update({odoo_field.name: value.split('+')[0].replace('T', ' ')})
                                elif odoo_field.ttype == 'selection':
                                    vals.update({odoo_field.name: value})
                                elif odoo_field.ttype == 'boolean':
                                    vals.update({odoo_field.name: value == 'true' if value else False})
                                else:
                                    vals.update({odoo_field.name: value})
                            # /!\ NOTE: Adding Unmapped fields as NOTES
                            for name, value in unmapped_fields:
                                notes.append('%s: %s' % (name, value))

                            vals.update({
                                'fb_lead_id': lead['id'],
                                'name': '%s - %s' % (form.name, lead['id']),
                                'description': "\n".join(notes),
                                'lead_form_id': form.id,
                                'fb_page_id': form.fb_page_id.id,
                                'medium_id': medium_id.id,
                                'source_id': source_id.id,
                            })
                            rec = self.create(vals)
                            _logger.info('Lead created - %s' % rec.id)
