# -*- coding: utf-8 -*-
# Copyright 2020 - Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

import logging
import requests

_logger = logging.getLogger(__name__)


class FacebookCredentials(models.Model):
    _name = 'fb.credentials'
    _description = "Facebook User authentication token and credentials"

    name = fields.Char(string="Name", required=True)
    user_access_id = fields.Char(string="User Access Id", required=True, help="App-scoped User ID")
    user_access_token = fields.Text(string="User Access Token", required=True)
    fb_page_ids = fields.One2many('fb.page', 'fb_credential_id', string="Facebook Pages")

    def sync_pages(self, resp):
        if not resp.get('data'):
            return
        for page in resp['data']:
            if self.fb_page_ids.filtered(lambda f: f.page_id == page['id']):
                continue
            self.env['fb.page'].create({
                'name': page['name'],
                'page_id': page['id'],
                'page_access_token': page['access_token'],
                'fb_credential_id': self.id})
        if resp.get('paging') and resp['paging'].get('next'):
            self.sync_pages(requests.get(resp['paging']['next']).json())
        return

    def get_pages(self):
        resp = requests.get("https://graph.facebook.com/v15.0/" + self.user_access_id + "/accounts",
                            params={'access_token': self.user_access_token, 'fields': 'name,id,access_token'}).json()
        if resp.get('error'):
            raise ValidationError(resp['error']['message'])
        self.sync_pages(resp)


class FacebookPage(models.Model):
    _name = 'fb.page'
    _description = "Facebook pages and it's credentials"

    name = fields.Char(string="Page Name", required=True)
    page_id = fields.Char(string="Page Id", required=True)
    page_access_token = fields.Char(string="Page Access Token", required=True)
    fb_lead_form_ids = fields.One2many('fb.lead.form', 'fb_page_id', string="Facebook Pages")
    fb_credential_id = fields.Many2one('fb.credentials')

    def sync_lead_forms(self, resp):
        if not resp.get('data'):
            return
        for lead_form in resp['data']:
            if self.fb_lead_form_ids.filtered(lambda f: f.form_id == lead_form['id']):
                continue
            if lead_form['status'] == 'ACTIVE':
                self.env['fb.lead.form'].create({
                    'name': lead_form['name'],
                    'form_id': lead_form['id'],
                    'fb_page_id': self.id}).get_lead_fields()
        if resp.get('paging') and resp['paging'].get('next'):
            self.sync_lead_forms(requests.get(resp['paging']['next']).json())
        return

    def get_lead_form(self):
        resp = requests.get("https://graph.facebook.com/v15.0/" + self.page_id + "/leadgen_forms",
                            params={'access_token': self.page_access_token, 'fields': 'name,id,status'}).json()
        if resp.get('error'):
            raise ValidationError(resp['error']['message'])
        self.sync_lead_forms(resp)


class FbLeadForm(models.Model):
    _name = 'fb.lead.form'
    _description = "Facebook page lead form"

    name = fields.Char(string="Form Name", required=True)
    form_id = fields.Char(string="Form Id", required=True)
    fb_page_id = fields.Many2one('fb.page', readonly=True, ondelete='cascade',
                                 string='Facebook Page')

    map_ids = fields.One2many('fb.lead.form.field', 'form_id')
    count = fields.Integer(string="Count")
    user_id = fields.Many2one('res.users', string='Salesperson', default=lambda self: self.env.user,
                              domain="[('share', '=', False)]", index=True)
    tag_ids = fields.Many2many('crm.tag', string="Tags")
    lead_interest_id = fields.Many2one('lead.interest','Lead Interest')

    def get_lead_fields(self):
        self.map_ids.unlink()
        resp = requests.get("https://graph.facebook.com/v15.0/" + self.form_id,
                            params={'access_token': self.fb_page_id.page_access_token, 'fields': 'questions'}).json()
        if resp.get('error'):
            raise ValidationError(resp['error']['message'])
        if resp.get('questions'):
            for question in resp.get('questions'):
                self.env['fb.lead.form.field'].create({
                    'form_id': self.id,
                    'name': question['label'],
                    'lead_field': question['key'],
                    'odoo_field': self.env['lead.form.default.mapping'].search([
                        ('lead_field', '=', question['key'])], limit=1)
                                  and self.env['lead.form.default.mapping'].search([
                        ('lead_field', '=', question['key'])], limit=1).odoo_field.id or ''
                })

    def auto_mapping_fields(self):
        for rec in self:
            rec.map_ids.auto_mapping()

    def create_lead(self, lead):
        vals, notes = {}, []
        # /!\ NOTE: List of mapped fields
        field_mapping = self.map_ids.filtered(lambda m: m.odoo_field).mapped('lead_field')
        unmapped_fields = []
        for name, value in lead.items():
            # /!\ NOTE: Unmapped fields
            if name not in field_mapping:
                unmapped_fields.append((name, value))
                continue
            odoo_field = self.map_ids.filtered(lambda m: m.lead_field == name).odoo_field
            # notes.append('%s: %s' % (odoo_field.field_description, value))
            if odoo_field.ttype == 'many2one':
                related_value = self.env[odoo_field.relation].search([('display_name', '=', value)])
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

        # /!\ NOTE: Appending Unmapped fields
        for name, value in unmapped_fields:
            notes.append('%s: %s' % (name, value))

        medium_id = self.env['utm.medium'].search([('name', '=', 'Facebook')], limit=1)
        source_id = self.env['utm.source'].search([('name', '=', 'Facebook')], limit=1)
        vals.update({
            'fb_lead_id': lead['id'],
            'name': '%s - %s' % (self.name, lead['id']),
            'description': "\n".join(notes),
            'lead_form_id': self.id,
            'fb_page_id': self.fb_page_id.id,
            # 'lead_source': 'Facebook',
            'medium_id': medium_id.id,
            'source_id': source_id.id,
            'user_id': self.user_id.id,
            'tag_ids': self.tag_ids.ids
        })
        return self.env['crm.lead'].create(vals)

    def collect_lead(self, resp):
        count = 0
        if not resp.get('data'):
            return
        for lead in resp['data']:
            field_data = lead.pop('field_data')
            lead_data = dict(lead)
            lead_data.update([(l['name'], l['values'][0])
                              for l in field_data
                              if l.get('name') and l.get('values')])
            lead = lead_data
            is_any_lead = self.env['crm.lead'].sudo().search(
                [('fb_lead_id', '=', lead.get('id')), '|', ('active', '=', True), ('active', '=', False)], limit=1)
            if not is_any_lead:
                self.create_lead(lead)
                count = count + 1
                self.count = count

        try:
            self.env.cr.commit()
        except Exception:
            self.env.cr.rollback()
        # /!\ NOTE: Checking Is it any next page ?
        if resp.get('paging') and resp['paging'].get('next'):
            self.collect_lead(requests.get(resp['paging']['next']).json())
        return

    def fetch_facebook_leads(self):
        resp = requests.get("https://graph.facebook.com/v15.0/" + self.form_id + "/leads",
                            params={'access_token': self.fb_page_id.page_access_token,
                                    'fields': 'created_time,field_data,is_organic'}).json()
        if resp.get('error'):
            raise UserError(resp['error']['message'])
        self.collect_lead(resp)
        _logger.info('Lead collected.')
        return self.lead_alert()

    def lead_alert(self):
        count = self.count
        message = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'title': ('Success !'),
                'message': str(count) + " Lead Created.",
                'sticky': False,
            }
        }
        self.count = 0
        return message


class FbLeadFields(models.Model):
    _name = 'fb.lead.form.field'
    _description = "Facebook form Lead fields"

    _sql_constraints = [('fb_lead_unique_mapping', 'CHECK(1=1)',
                         'Default fields mapping must be unique')]

    name = fields.Char(string="Name")
    lead_field = fields.Char(string="Lead Field")
    form_id = fields.Many2one('fb.lead.form', required=True, ondelete='cascade', string='FB Lead Form')
    odoo_field = fields.Many2one('ir.model.fields',
                                 domain=[('model', '=', 'crm.lead'),
                                         ('store', '=', True),
                                         ('ttype', 'in', ('char',
                                                          'date',
                                                          'datetime',
                                                          'float',
                                                          'html',
                                                          'integer',
                                                          'monetary',
                                                          'many2one',
                                                          'selection',
                                                          'phone',
                                                          'text'))], string="CRM Field")

    def auto_mapping(self):
        for rec in self:
            matched = self.env['lead.form.default.mapping'].search([('lead_field', '=', rec.lead_field)],
                                                                   limit=1)
            if matched:
                rec.odoo_field = matched.odoo_field


class LeadFieldMapping(models.Model):
    _name = 'lead.form.default.mapping'
    _description = 'Default or General mapping of lead form'
    _rec_name = 'lead_field'

    _sql_constraints = [('lead_unique_mapping', 'unique(odoo_field, lead_field)',
                         'Default fields mapping must be unique')]

    lead_field = fields.Char(required=True)
    odoo_field = fields.Many2one('ir.model.fields', ondelete='set default',
                                 domain=[('model', '=', 'crm.lead'),
                                         ('store', '=', True),
                                         ('ttype', 'in', ('char',
                                                          'date',
                                                          'datetime',
                                                          'float',
                                                          'html',
                                                          'integer',
                                                          'monetary',
                                                          'many2one',
                                                          'selection',
                                                          'phone',
                                                          'text'))],
                                 required=True, string="CRM Field")
