# -*- coding: utf-8 -*-
from email.policy import default

from odoo import fields, models, api, _

TICKET_PRIORITY = [
    ('0', 'Trivial'),
    ('1', 'Low priority'),
    ('2', 'Medium priority'),
    ('3', 'High priority'),
    # ('3', 'Urgent'),
]


class HelpdeskSLA(models.Model):
    _name = "helpdesk.sla"
    _order = "name"
    _description = "Helpdesk SLA Policies"

    name = fields.Char(required=True)
    description = fields.Html(string='SLA Policy Description')
    active = fields.Boolean(string="Active", default=True)
    team_id = fields.Many2one('helpdesk.ticket.team', string="Helpdesk Team", required=True)
    type_ids = fields.Many2many('helpdesk.ticket.type', string="Types")
    tag_ids = fields.Many2many('helpdesk.ticket.tag', string="Tags")
    priority = fields.Selection(
        TICKET_PRIORITY, string='Priority',
        default='0', required=True)
    partner_ids = fields.Many2many(
        'res.partner', string="Customers")
    company_id = fields.Many2one('res.company', string="Company", related='team_id.company_id')
    time = fields.Float('Within', default=0, required=True,
                        help='Maximum number of working hours a ticket should take to reach the target stage, starting from the date it was created.')
    stage_id = fields.Many2one(
        'helpdesk.ticket.stage', 'Target Stage',
        help='Minimum stage a ticket needs to reach in order to satisfy this SLA.', required=True)

    exclude_stage_ids = fields.Many2one('helpdesk.ticket.stage', string="Excluding Stage",
                                        copy=True,
                                        help="The time spent in these stages won't be taken into account in the calculation of the SLA.")

    ticket_count = fields.Integer(string="Ticket", compute="_compute_ticket_count")


    response_time = fields.Float('Response Time')

    @api.depends('team_id')
    @api.depends_context('with_team_name')
    def _compute_display_name(self):
        if not self._context.get('with_team_name'):
            return super()._compute_display_name()
        for sla in self:
            sla.display_name = f'{sla.name} - {sla.team_id.name}'

    def _compute_ticket_count(self):
        res = self.env['helpdesk.ticket']._read_group(
            [('sla_ids', 'in', self.ids), ('stage_id.fold', '=', False)],
            ['sla_ids'], ['__count'])
        sla_data = {sla.id: count for sla, count in res}
        for sla in self:
            sla.ticket_count = sla_data.get(sla.id, 0)

    def action_open_helpdesk_ticket(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'All Tickets',
            'view_mode': 'tree,form',
            'res_model': 'helpdesk.ticket',
            'domain': [('sla_ids', 'in', self.ids)],
            'context': "{'create': False}"
        }
