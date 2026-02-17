# from AptUrl.Helpers import _
from bs4 import BeautifulSoup
from odoo import fields, models, api
from odoo.exceptions import ValidationError


class Lead(models.Model):
    _inherit = 'crm.lead'
    ticket_count = fields.Integer('Ticket Count', compute='count_ticket')
    ticket_ids = fields.One2many('helpdesk.ticket', 'lead_id', string='Ticket')


    def clean_html(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        # Remove empty paragraphs
        for p_tag in soup.find_all('p'):
            if not p_tag.text.strip():
                p_tag.decompose()
        return str(soup)

    def create_ticket(self):
        params = self.env['ir.config_parameter'].sudo()
        v = params.get_param('helpdesk_mgmt.auto.teams')
        cleaned_html = False
        if self.description:
            cleaned_html = self.clean_html(self.description)
        fieldname = self.env['ir.config_parameter'].sudo().get_param('helpdesk_ticket.teams_id')
        team = self.env['helpdesk.ticket.team'].browse(int(fieldname))

        if not cleaned_html:
            raise ValidationError("Add Internal notes")

        vals = {
            'name': self.name,
            'partner_name': self.partner_name or self.partner_id and self.partner_id.name,
            'partner_email': self.email_from,
            'team_id': team.id,
            'partner_id': self.partner_id and self.partner_id.id,
            'user_id': team.user_id.id,
            'description': cleaned_html,
            'lead_id': self.id}
        self.env['helpdesk.ticket'].create(vals)

    def get_ticket(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tickets',
            'view_mode': 'tree,form',
            'res_model': 'helpdesk.ticket',
            'domain': [('lead_id', '=', self.id)],
            'context': "{'create': False}"
        }


    # def count_ticket(self):
    #     for record in self:
    #         record.ticket_count = self.env['helpdesk.ticket'].search_count(
    #             [('lead_id', '=', self.id)])

    def count_ticket(self):
        for record in self:
            record.ticket_count = len(record.ticket_ids)
