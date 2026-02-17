from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval
from odoo.tools import float_round
import datetime

from dateutil import relativedelta
from collections import defaultdict
from odoo.osv import expression


class HelpdeskTeam(models.Model):
    _name = "helpdesk.ticket.team"
    _description = "Helpdesk Ticket Team"
    _inherit = ["mail.thread", "mail.alias.mixin"]

    name = fields.Char(required=True)
    user_ids = fields.Many2many(comodel_name="res.users", string="Members")
    active = fields.Boolean(default=True)
    category_ids = fields.Many2many(
        comodel_name="helpdesk.ticket.category", string="Category"
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
    )
    company_ids = fields.Many2many(
        comodel_name="res.company",
        string="Companies",default=lambda self: self.env.company,

    )
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="Team Leader",
        check_company=True,
    )
    alias_id = fields.Many2one(
        comodel_name="mail.alias",
        string="Email",
        ondelete="restrict",
        required=True,
        help="The email address associated with \
                               this channel. New emails received will \
                               automatically create new tickets assigned \
                               to the channel.",
    )
    color = fields.Integer(string="Color Index", default=0)
    ticket_ids = fields.One2many(
        comodel_name="helpdesk.ticket",
        inverse_name="team_id",
        string="Tickets",
    )

    todo_ticket_count = fields.Integer(
        string="Number of tickets", compute="_compute_todo_tickets"
    )
    todo_ticket_count_unassigned = fields.Integer(
        string="Number of tickets unassigned", compute="_compute_todo_tickets"
    )
    todo_ticket_count_unattended = fields.Integer(
        string="Number of tickets unattended", compute="_compute_todo_tickets"
    )
    todo_ticket_count_high_priority = fields.Integer(
        string="Number of tickets in high priority", compute="_compute_todo_tickets"
    )
    use_helpdesk_timesheet = fields.Boolean(
        'Timesheets',
        store=True, readonly=False)
    # use_helpdesk_timesheet = fields.Boolean(
    #     'Timesheets', compute='_compute_use_helpdesk_timesheet',
    #     store=True, readonly=False)


    @api.depends('company_id')
    def compute_company(self):
        for rec in self:
            if rec.company_id:
                rec.write({'company_ids': [(6, 0, [rec.company_id.id])]})

    # use_helpdesk_sale_timesheet = fields.Boolean(
    #     'Time Billing', compute='_compute_use_helpdesk_sale_timesheet', store=True,
    #     readonly=False)
    use_helpdesk_sale_timesheet = fields.Boolean(
        'Time Billing',
        readonly=False)
    success_rate = fields.Float(string='Success Rate', compute='_compute_success_rate')

    def _compute_success_rate(self):
        dt = datetime.datetime.combine(datetime.date.today() - relativedelta.relativedelta(days=6), datetime.time.min)
        sla_teams = self.filtered('use_sla')
        domain = [
            ('team_id', 'in', sla_teams.ids),
            '|', ('stage_id.fold', '=', True)
        ]

        sla_tickets_and_failed_tickets_per_team = defaultdict(lambda: [0, 0])
        today = fields.Datetime.now()
        tickets_sla_count = self.env['helpdesk.ticket']._read_group(domain + [
            '|', ('sla_reached', '=', True), ('sla_reached_late', '=', True)],
                                                                    ['team_id'], ['__count']
                                                                    )
        tickets_success_count = self.env['helpdesk.ticket']._read_group(domain + [
            '|', ('sla_deadline', '<', today), ('sla_reached_late', '=', True)],
                                                                        ['team_id'], ['__count']
                                                                        )
        for team, team_count in tickets_sla_count:
            sla_tickets_and_failed_tickets_per_team[team.id][0] = team_count
        for team, team_count in tickets_success_count:
            sla_tickets_and_failed_tickets_per_team[team.id][1] = team_count
        for team in sla_teams:
            if not sla_tickets_and_failed_tickets_per_team.get(team.id):
                team.success_rate = -1
                continue
            total_count = sla_tickets_and_failed_tickets_per_team[team.id][0]
            success_count = total_count - sla_tickets_and_failed_tickets_per_team[team.id][1]
            team.success_rate = float_round(success_count * 100 / total_count, 2) if total_count else 0.0
        (self - sla_teams).success_rate = -1

    # @api.depends('use_helpdesk_timesheet')
    # def _compute_use_helpdesk_sale_timesheet(self):
    #     without_timesheet = self.filtered(lambda t: not t.use_helpdesk_timesheet)
    #     without_timesheet.update({'use_helpdesk_sale_timesheet': False})

    # @api.depends('use_helpdesk_sale_timesheet')
    # def _compute_use_helpdesk_timesheet(self):
    #     sale_timesheet = self.filtered('use_helpdesk_sale_timesheet')
    #     sale_timesheet.update({'use_helpdesk_timesheet': True})

    @api.depends("ticket_ids", "ticket_ids.stage_id")
    def _compute_todo_tickets(self):
        ticket_model = self.env["helpdesk.ticket"]
        fetch_data = ticket_model.read_group(
            [("team_id", "in", self.ids), ("closed", "=", False)],
            ["team_id", "user_id", "unattended", "priority"],
            ["team_id", "user_id", "unattended", "priority"],
            lazy=False,
        )
        result = [
            [
                data["team_id"][0],
                data["user_id"] and data["user_id"][0],
                data["unattended"],
                data["priority"],
                data["__count"],
            ]
            for data in fetch_data
        ]
        for team in self:
            team.todo_ticket_count = sum(r[4] for r in result if r[0] == team.id)
            team.todo_ticket_count_unassigned = sum(
                r[4] for r in result if r[0] == team.id and not r[1]
            )
            team.todo_ticket_count_unattended = sum(
                r[4] for r in result if r[0] == team.id and r[2]
            )
            team.todo_ticket_count_high_priority = sum(
                r[4] for r in result if r[0] == team.id and r[3] == "3"
            )

    def _alias_get_creation_values(self):
        values = super()._alias_get_creation_values()
        values["alias_model_id"] = self.env.ref(
            "helpdesk_mgmt.model_helpdesk_ticket"
        ).id
        values["alias_defaults"] = defaults = safe_eval(self.alias_defaults or "{}")
        defaults["team_id"] = self.id
        return values

    # def action_view_ticket(self):
    #     action = self.env["ir.actions.actions"]._for_xml_id("helpdesk_mgmt.helpdesk_ticket_team_action")
    #     action['display_name'] = self.name
    #     return action
    #
    # def _get_action_view_ticket_params(self, is_ticket_closed=False):
    #     """ Get common params for the actions
    #
    #         :param is_ticket_closed: Boolean if True, then we want to see the tickets closed in last 7 days
    #         :returns dict containing the params to update into the action.
    #     """
    #     domain = [
    #         '&',
    #         ('stage_id.fold', '=', is_ticket_closed),
    #         ('team_id', 'in', self.ids),
    #     ]
    #     context = {
    #         'search_default_is_open': not is_ticket_closed,
    #         'default_team_id': self.id,
    #     }
    #     view_mode = 'tree,kanban,form,activity,pivot,graph'
    #     if is_ticket_closed:
    #         domain = expression.AND([domain, [
    #             ('close_date', '>=', datetime.date.today() - datetime.timedelta(days=6)),
    #         ]])
    #         context.update(search_default_closed_last_7days=True)
    #     return {
    #         'domain': domain,
    #         'context': context,
    #         'view_mode': view_mode,
    #     }
    #
    # def action_view_success_rate(self):
    #     action = self.action_view_ticket()
    #     print(action,'actionssssssssssssss')
    #     action_params = self._get_action_view_ticket_params(True)
    #     print(action_params,'action_params')
    #     action.update(
    #         domain=expression.AND([
    #             action_params['domain'],
    #             [('team_id', 'in', self.ids)],
    #         ]),
    #         context={
    #             **action_params['context'],
    #             'search_default_sla_success': True,
    #         },
    #         view_mode=action_params['view_mode'],
    #         views=[(False, view) for view in action_params['view_mode'].split(",")],
    #     )
    #     print(action,'action_view_success_rateaction_view_success_rate')
    #     return action
