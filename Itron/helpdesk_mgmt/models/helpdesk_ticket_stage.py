from odoo import fields, models, api


class HelpdeskTicketStage(models.Model):
    _name = "helpdesk.ticket.stage"
    _description = "Helpdesk Ticket Stage"
    _order = "sequence, id"

    @api.model
    def default_get(self, fields):
        print(self.env.context)
        if 'default_team_id' in self.env.context:
            ctx = dict(self.env.context)
            ctx.pop('default_team_id')
            self = self.with_context(ctx)
        res = super(HelpdeskTicketStage, self).default_get(fields)
        print(res,'resssss')
        return res

    name = fields.Char(string="Stage Name", required=True, translate=True)
    team_id = fields.Many2one('helpdesk.ticket.team', string='Help Team',
                              help='Specific team that uses this stage. Other teams will not be able to see or use '
                                   'this stage.')
    description = fields.Html(translate=True, sanitize_style=True)
    sequence = fields.Integer(default=1)
    active = fields.Boolean(default=True)
    unattended = fields.Boolean()
    closed = fields.Boolean()
    rejected = fields.Boolean()
    returned = fields.Boolean()
    is_email = fields.Boolean('Email Notification')
    mail_template_id = fields.Many2one(
        comodel_name="mail.template",
        string="Email Template",
        domain=[("model", "=", "helpdesk.ticket")],
        help="If set an email will be sent to the "
             "customer when the ticket"
             "reaches this step.",
    )
    fold = fields.Boolean(
        string="Folded in Kanban",
        help="This stage is folded in the kanban view "
             "when there are no records in that stage "
             "to display.",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
    )
    help_team_ids = fields.Many2many(
        'helpdesk.ticket.team', relation='team_stage_rec', string='Helpdesk Teams')

