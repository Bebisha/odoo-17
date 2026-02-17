# -*- coding: utf-8 -*-
import json

from odoo import fields, models, _


class KgLead(models.Model):
    _name = "kg.lead"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Kg Lead"
    _order = 'name desc'

    name = fields.Char(string='Reference', required=True)

    def _get_portal_partner_domain(self):
        portal_group = self.env.ref('base.group_portal')
        portal_users = self.env['res.users'].sudo().search([('groups_id', 'in', [portal_group.id])])
        return [('id', 'in', portal_users.mapped('partner_id').ids)]

    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        domain=_get_portal_partner_domain
    )
    lead_id = fields.Many2one('crm.lead','Lead', copy=False)
    date = fields.Date(string="Date", default=lambda self: fields.Date.context_today(self))
    description = fields.Html("Description")
    total_effort = fields.Float("Total Effort", copy=False)
    source_id = fields.Many2one('utm.source', string='Source', default=lambda self: self.env.ref('kg_lead.utm_source_change_request').id, readonly=True)
    lead_interest_id = fields.Many2one('lead.interest', 'Lead Interest')
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company)
    state = fields.Selection([('draft', 'Draft'), ('lead_created', 'Lead Created')], default='draft')
    attachment_ids = fields.Many2many(
        comodel_name='ir.attachment',
        string="Attachments", copy=False
    )
    updated_attachments = fields.Char('Updated Attachment IDs', copy=False)
    priority = fields.Selection(
        selection=[
            ("0", "Low"),
            ("1", "Medium"),
            ("2", "High"),
        ],
        default="1",
    )

    def write(self, vals):
        res = super(KgLead, self).write(vals)
        if vals.get('attachment_ids') and self.lead_id:
            self.update_attachments()
        return res

    def get_lead_url(self):
        """Generate the URL for approvers to view the material request"""
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return f"{base_url}/web#id={self.lead_id.id}&view_type=form&model=crm.lead"



    def update_attachments(self):
        existing_ids = json.loads(self.updated_attachments) if self.updated_attachments else []
        not_updated_att_ids = self.attachment_ids.filtered(lambda x: x.id not in existing_ids).ids
        self.updated_attachments = json.dumps(self.attachment_ids.ids)
        if not_updated_att_ids:
            if self.lead_id and not_updated_att_ids:
                for attachment in not_updated_att_ids:
                    self.sudo().lead_id.message_post(
                        body="New attachment added.",
                        attachment_ids=[attachment]
                    )
                subject = _("New document is added")
                body = _(
                    """
                    <p>Dear Sales Team,</p>
                    <p>A new attachment has been added to the lead.</p>
                    <p><strong>Details:</strong></p>
                    <ul>
                        <li><strong>Customer:</strong> %s</li>
                        <li><strong>Reference:</strong> %s</li>
                        <li><strong>Lead Interest:</strong> %s</li>
                        <li><strong>Lead Source:</strong> %s</li>
                    </ul>
                    <p>Please review the lead and take the necessary action.</p>
                    <p><a href="%s">VIEW LEAD</a></p>
                    <p>Thank you.</p>
                    """
                ) % (
                           self.partner_id.name or '',
                           self.name or '',
                           self.lead_interest_id.name or '',
                           self.source_id.name or '',
                           self.get_lead_url(),
                       )

                # Get sender email
                mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
                email_from = mail_server.smtp_user if mail_server else self.env.user.email

                mail_values = {
                    'subject': subject,
                    'body_html': body,
                    'email_to': 'sales@klystronglobal.com',
                    'email_from': email_from,
                }

                self.env['mail.mail'].sudo().create(mail_values).send()

            self.message_post(body="Newly added attachment updated in the lead")

    def action_create_lead(self):
        stage_id = self.env['crm.stage'].search([('is_opportunity', '=', True)], limit=1)
        lead = self.env['crm.lead'].sudo().create({
            'name': self.name,
            'partner_id': self.partner_id.id,
            'contact_name': self.partner_id.name,
            'email_from': self.partner_id.email,
            'phone': self.partner_id.phone,
            'description': self.description,
            'country': self.company_id.country_id.name,
            'source_id': self.source_id.id,
            'priority': self.priority,
            'lead_interest_id': self.lead_interest_id.id,
            'type': 'opportunity',
            'is_change_req': True,
            'total_effort': self.total_effort,
            'team_id': 23,
            'company_id': 2,
            'user_id': False,
            'stage_id': stage_id.id

        })
        self.lead_id = lead.id
        self.state = 'lead_created'

        self.update_attachments()

        subject = _("New lead created in opportunity stage")
        body = _(
            """
            <p>Dear Sales Team,</p>
            <p>A new lead has been submitted by <strong>%s</strong> and is currently in the Opportunity stage.</p>
            <p><strong>Details:</strong></p>
            <ul>
                <li>Customer: %s</li>
                <li>Reference: %s</li>
                <li>Date: %s</li>
                <li>Lead Interest: %s</li>
                <li>Lead Source: %s</li>
            </ul>
            <p>Kindly review the lead and take the necessary action.</p>
            <p><a href="%s">VIEW LEAD</a></p>
            <p>Thank you.</p>
            """
        ) % (
                   self.create_uid.name,
                   self.partner_id.name,
                   self.name,
                   self.date,
                   self.lead_interest_id.name,
                   self.source_id.name,
                   self.get_lead_url(),
               )

        outgoing_mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
        email_from = outgoing_mail_server.sudo().smtp_user if outgoing_mail_server else self.env.user.email

        mail_values = {
            'subject': subject,
            'body_html': body,
            'email_to': 'sales@klystronglobal.com',
            'email_from': email_from,
        }

        self.env['mail.mail'].sudo().create(mail_values).send()

    def action_view_leads(self):
        action = {
            "type": "ir.actions.act_window",
            "res_model": "crm.lead",
            "name": _("Leads"),
            "context": {"create": False},
            "view_mode": "tree,form",
            "views": [(False, 'tree'), (False, 'form')],
            "target": "current",
            "domain": [('id', 'in', self.lead_id.ids)],
        }
        return action


