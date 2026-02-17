from email.policy import default

from odoo import fields, models, api, _


class HelpdeskTicketTeam(models.Model):
    _inherit = 'helpdesk.ticket.team'

    use_sla = fields.Boolean('SLA Policies', default=True)

    resource_calendar_id = fields.Many2one('resource.calendar', 'Working Hours',
                                           default=lambda self: self.env.company.resource_calendar_id,
                                           # domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                           help="Working hours used to determine the deadline of SLA Policies.")
