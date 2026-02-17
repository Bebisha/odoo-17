import pytz

from odoo import _, api, fields, models, tools
from odoo.osv import expression
from odoo.exceptions import AccessError, UserError
from datetime import datetime, time, timedelta



class HelpdeskTicket(models.Model):
    _name = "helpdesk.ticket"
    _description = "Helpdesk Ticket"
    _rec_name = "number"
    _order = "priority desc, number desc, id desc"
    _mail_post_access = "read"
    _inherit = ["mail.thread.cc", "mail.activity.mixin", "portal.mixin"]

    def _get_default_stage_id(self):
        print(self.team_id.id)
        # v = self.env["helpdesk.ticket.stage"].search(['team_id','=',self.team_id.id], limit=1).id
        return self.env["helpdesk.ticket.stage"].search([], limit=1).id

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        team_id = self._context.get('default_team_id')
        if team_id:
            search_domain = ['|', ('id', 'in', stages.ids), '|', ('team_id', '=', False), ('team_id', '=', team_id)]
        else:
            search_domain = ['|', ('id', 'in', stages.ids), ('team_id', '=', False)]

        # perform search
        stage_ids = stages._search(search_domain, order=order)
        return stages.browse(stage_ids)
        # stage_ids = self.env["helpdesk.ticket.stage"].search([])
        # return stage_ids

    number = fields.Char(string="Ticket number", default="/", readonly=True)
    data_collection = fields.Char(string='Data Collection')
    training_date = fields.Date(string='Reported Date')
    go_live_date = fields.Date(string='Go Live Date')
    name = fields.Char(string="Title", required=True)
    description = fields.Html(required=True, sanitize_style=True)
    user_id = fields.Many2one(
        comodel_name="res.users", string="Assigned user", tracking=True, index=True
    )
    user_ids = fields.Many2many(
        comodel_name="res.users", related="team_id.user_ids", string="Users"
    )
    company_ids = fields.Many2many(
        comodel_name="res.company",  string="Companies",default=lambda self: self.env.company
    )
    lead_id = fields.Many2one('crm.lead')
    stage_id = fields.Many2one(
        comodel_name="helpdesk.ticket.stage",
        compute="_compute_stage_id",
        string="Stage",
        group_expand="_read_group_stage_ids",
        default=_get_default_stage_id,
        tracking=True,
        ondelete="restrict",
        index=True,
        copy=False,
        domain="['|', ('team_id', '=', False), ('team_id', '=', team_id)]",
        store=True,
        readonly=False
    )
    # stage_id = fields.Many2one(
    #     'crm.stage', string='Stage', index=True, tracking=True,
    #     compute='_compute_stage_id', readonly=False, store=True,
    #     copy=False, group_expand='_read_group_stage_ids', ondelete='restrict',
    #     domain="['|', ('team_id', '=', False), ('team_id', '=', team_id)]")
    partner_id = fields.Many2one(comodel_name="res.partner", string="Contact")
    partner_name = fields.Char()
    partner_email = fields.Char(string="Email")

    last_stage_update = fields.Datetime(default=fields.Datetime.now)
    assigned_date = fields.Datetime()
    closed_date = fields.Datetime()
    closed = fields.Boolean(related="stage_id.closed")
    unattended = fields.Boolean(related="stage_id.unattended", store=True)
    tag_ids = fields.Many2many(comodel_name="helpdesk.ticket.tag", string="Tags")
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
    channel_id = fields.Many2one(
        comodel_name="helpdesk.ticket.channel",
        string="Channel",
        help="Channel indicates where the source of a ticket"
             "comes from (it could be a phone call, an email...)",
    )
    category_id = fields.Many2one(
        comodel_name="helpdesk.ticket.category",
        string="Category",
    )
    application_id = fields.Many2one(
        comodel_name="helpdesk.ticket.application",
        string="Application",
    )
    team_id = fields.Many2one(
        comodel_name="helpdesk.ticket.team",
        string="Team",
    )
    priority = fields.Selection(
        selection=[
            ('0', 'Trivial'),
            ('1', 'Low priority'),
            ('2', 'Medium priority'),
            ('3', 'High priority'),
        ],
        default="1",
    )
    attachment_ids = fields.One2many(
        comodel_name="ir.attachment",
        inverse_name="res_id",
        domain=[("res_model", "=", "helpdesk.ticket")],
        string="Media Attachments",
    )
    color = fields.Integer(string="Color Index")
    kanban_state = fields.Selection(
        selection=[
            ("normal", "Default"),
            ("done", "Ready for next stage"),
            ("blocked", "Blocked"),
        ],
    )
    active = fields.Boolean(default=True)
    reject_reason = fields.Char(string="Reject Reason")
    return_reason = fields.Char(string="Return Reason")
    rejected = fields.Boolean(related="stage_id.rejected")
    returned = fields.Boolean(related="stage_id.returned")

    @api.onchange('stage_id')
    def onchange_stage_id_reject(self):
        for ticket in self:
            if ticket.rejected:
                if not ticket.reject_reason:
                    raise (UserError("Please enter rejection reason!"))

    @api.onchange('stage_id')
    def onchange_stage_id_reject(self):
        for ticket in self:
            if ticket.returned:
                if not ticket.return_reason:
                    raise (UserError("Please enter return reason!"))

    @api.depends('company_id')
    def onchange_company_id(self):
        for ticket in self:
            if ticket.company_id:
                ticket.write({'company_ids': [(6, 0, [ticket.company_id.id])]})

    @api.onchange('user_id')
    def onchange_user_id(self):
        for ticket in self:
            if ticket.user_id and ticket.user_id.company_id:
                ticket.write({'company_ids': [(4, ticket.user_id.company_id.id)]})

    @api.depends('team_id')
    def _compute_stage_id(self):
        for lead in self:
            if not lead.stage_id:
                lead.stage_id = lead._stage_find().id

    def _stage_find(self, team_id=False, domain=None, order='sequence, id', limit=1):
        """ Determine the stage of the current lead with its teams, the given domain and the given team_id
            :param team_id
            :param domain : base search domain for stage
            :param order : base search order for stage
            :param limit : base search limit for stage
            :returns crm.stage recordset
        """
        # collect all team_ids by adding given one, and the ones related to the current leads
        team_ids = set()
        if team_id:
            team_ids.add(team_id)
        for lead in self:
            if lead.team_id:
                team_ids.add(lead.team_id.id)
        # generate the domain
        if team_ids:
            search_domain = ['|', ('team_id', '=', False), ('team_id', 'in', list(team_ids))]
        else:
            search_domain = [('team_id', '=', False)]
        # AND with the domain in parameter
        if domain:
            search_domain += list(domain)
        # perform search, return the first found
        return self.env['crm.stage'].search(search_domain, order=order, limit=limit)

    def send_user_mail(self):
        self.env.ref("helpdesk_mgmt.assignment_email_template").send_mail(self.id)

    def change_stage_req_mail(self):
        self.env.ref("helpdesk_mgmt.email_template_data_request").send_mail(self.id)

    def change_stage_rejected_mail(self):
        self.env.ref("helpdesk_mgmt.rejected_ticket_template_users_id").send_mail(self.id)

    def change_stage_conf_mail(self):
        self.env.ref("helpdesk_mgmt.new_ticket_configuration_complete_template").send_mail(self.id)

    def change_stage_live_mail(self):
        self.env.ref("helpdesk_mgmt.new_ticket_go_live_template").send_mail(self.id)

    def change_stage_mail(self):
        self.env.ref("helpdesk_mgmt.new_ticket__transfer_template").send_mail(self.id)

    def send_partner_mail(self):
        helpdesk_emails_str = self.env.user.company_id.helpdesk_user_ids
        if helpdesk_emails_str:
            email_list = [email.strip() for email in helpdesk_emails_str.split(',') if email.strip()]
        else:
            email_list = []
        if email_list:
            email_to = ",".join(email_list)
            template = self.env.ref("helpdesk_mgmt.new_ticket_template")
            template.send_mail(self.id, force_send=True, email_values={'email_to': email_to})
        else:
            self.env.ref("helpdesk_mgmt.new_ticket_template").send_mail(self.id)


    def send_partner_user_mail(self,user):
        template = self.env.ref("helpdesk_mgmt.new_ticket_template_users")
        # You can send the email to the specific user directly

        template.send_mail(self.id, force_send=True, email_values={'email_to': user.email})

        # self.env.ref("helpdesk_mgmt.new_ticket_template_users").send_mail(self.id)

    def name_get(self):
        res = []
        for rec in self:
            res.append((rec.id, rec.number + " - " + rec.name))
        return res

    def assign_to_me(self):
        self.write({"user_id": self.env.user.id})

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        if self.partner_id:
            self.partner_name = self.partner_id.name
            self.partner_email = self.partner_id.email

    @api.onchange("team_id", "user_id")
    def _onchange_dominion_user_id(self):
        if self.user_id and self.user_ids and self.user_id not in self.team_id.user_ids:
            self.update({"user_id": False})
            return {"domain": {"user_id": []}}
        if self.team_id:
            return {"domain": {"user_id": [("id", "in", self.user_ids.ids)]}}
        else:
            return {"domain": {"user_id": []}}

    # ---------------------------------------------------
    # CRUD
    # ---------------------------------------------------

    @api.model
    def create(self, vals):
        if vals.get("number", "/") == "/":
            vals["number"] = self._prepare_ticket_number(vals)
        res = super(HelpdeskTicket, self).create(vals)

        if res.application_id and res.application_id.team_id:
            team = res.application_id.team_id
            res.team_id = team.id
            # res.user_id = team.user_id.id if team.user_id else False

        # Check if mail to the user has to be sent
        if res.user_id:
            res.send_user_mail()

        if vals.get("partner_id") and res:
            res.send_partner_mail()
            partner = self.env['res.partner'].browse(vals.get("partner_id"))

            helpdesk_users = partner.helpdesk_user_ids
            if helpdesk_users:
                for user in helpdesk_users:
                    res.send_partner_user_mail(user)

                # context: no_log, because subtype already handle this

                # make customer follower
        for ticket in res:
            if ticket.partner_id:
                ticket.message_subscribe(partner_ids=ticket.partner_id.ids)

            ticket._portal_ensure_token()

            # apply SLA
        res.sudo()._sla_apply()

        return res

    def copy(self, default=None):
        self.ensure_one()
        if default is None:
            default = {}
        if "number" not in default:
            default["number"] = self._prepare_ticket_number(default)
        res = super().copy(default)
        return res

    def write(self, vals):
        for _ticket in self:
            now = fields.Datetime.now()
            if vals.get("stage_id"):
                stage = self.env["helpdesk.ticket.stage"].browse([vals["stage_id"]])
                vals["last_stage_update"] = now
                if stage.closed:
                    vals["closed_date"] = now
            if vals.get("user_id"):
                vals["assigned_date"] = now

            # SLA business
            sla_triggers = self._sla_reset_trigger()
            if any(field_name in sla_triggers for field_name in vals.keys()):
                self.sudo()._sla_apply(keep_reached=True)
            if 'stage_id' in vals:
                self.sudo()._sla_reach(vals['stage_id'])

            if 'stage_id' in vals and self.env['helpdesk.ticket.stage'].browse(vals['stage_id']).fold:
                odoobot_partner_id = self.env['ir.model.data']._xmlid_to_res_id('base.partner_root')
                for ticket in self:
                    exceeded_hours = ticket.sla_status_ids.mapped('exceeded_hours')
                    if exceeded_hours:
                        min_hours = min([hours for hours in exceeded_hours if hours > 0], default=min(exceeded_hours))
                        message = _("This ticket was successfully closed %s hours before its SLA deadline.",
                                    round(abs(min_hours))) if min_hours < 0 \
                            else _("This ticket was closed %s hours after its SLA deadline.", round(min_hours))
                        ticket.message_post(body=message, subtype_xmlid="mail.mt_note", author_id=odoobot_partner_id)
        return super().write(vals)

    def _sla_reach(self, stage_id):
        """ Flag the SLA status of current ticket for the given stage_id as reached, and even the unreached SLA applied
            on stage having a sequence lower than the given one.
        """

        stage = self.env['helpdesk.ticket.stage'].browse(stage_id)
        stages = self.env['helpdesk.ticket.stage'].search([('sequence', '<=', stage.sequence), (
            'help_team_ids', 'in', self.mapped('team_id').ids)])  # take previous stages
        sla_status = self.env['helpdesk.sla.status'].search([('ticket_id', 'in', self.ids)])
        sla_not_reached = sla_status.filtered(lambda sla: not sla.reached_datetime and sla.sla_stage_id in stages)

        sla_not_reached.write({'reached_datetime': fields.Datetime.now()})
        (sla_status - sla_not_reached).filtered(lambda x: x.sla_stage_id not in stages).write(
            {'reached_datetime': False})
    def _sla_apply(self, keep_reached=False):

        """ Apply SLA to current tickets: erase the current SLAs, then find and link the new SLAs to each ticket.
            Note: transferring ticket to a team "not using SLA" (but with SLAs defined), SLA status of the ticket will be
            erased but nothing will be recreated.
            :returns recordset of new helpdesk.sla.status applied on current tickets
        """
        # get SLA to apply
        sla_per_tickets = self._sla_find()

        # generate values of new sla status
        sla_status_value_list = []
        for tickets, slas in sla_per_tickets.items():
            sla_status_value_list += tickets._sla_generate_status_values(slas, keep_reached=keep_reached)

        sla_status_to_remove = self.mapped('sla_status_ids')
        if keep_reached:  # keep only the reached one to avoid losing reached_date info
            sla_status_to_remove = sla_status_to_remove.filtered(lambda status: not status.reached_datetime)

        # unlink status and create the new ones in 2 operations
        sla_status_to_remove.unlink()
        stage = self.env['helpdesk.sla.status'].create(sla_status_value_list)
        return stage

    def _sla_find(self):
        """ Find the SLA to apply on the current tickets
            :returns a map with the tickets linked to the SLA to apply on them
            :rtype : dict {<helpdesk.ticket>: <helpdesk.sla>}
        """
        tickets_map = {}
        sla_domain_map = {}

        def _generate_key(ticket):
            """ Return a tuple identifying the combinaison of field determining the SLA to apply on the ticket """
            fields_list = self._sla_reset_trigger()
            key = list()
            for field_name in fields_list:
                if ticket._fields[field_name].type == 'many2one':
                    key.append(ticket[field_name].id)
                else:
                    key.append(ticket[field_name])
            return tuple(key)

        for ticket in self:
            if ticket.team_id.use_sla:  # limit to the team using SLA
                key = _generate_key(ticket)
                # group the ticket per key
                tickets_map.setdefault(key, self.env['helpdesk.ticket'])
                tickets_map[key] |= ticket
                # group the SLA to apply, by key
                if key not in sla_domain_map:
                    sla_domain_map[key] = expression.AND([[
                        ('team_id', '=', ticket.team_id.id), ('priority', '=', ticket.priority),
                        ('stage_id.sequence', '>=', ticket.stage_id.sequence),
                        '|', ('type_ids', 'in', ticket.ticket_type_id.ids), ('type_ids', '=', False)],
                        ticket._sla_find_extra_domain()])

        result = {}
        for key, tickets in tickets_map.items():  # only one search per ticket group
            domain = sla_domain_map[key]
            slas = self.env['helpdesk.sla'].search(domain)
            result[tickets] = slas.filtered(
                lambda s: not s.tag_ids or (tickets.tag_ids & s.tag_ids))  # SLA to apply on ticket subset
        return result

    @api.model
    def _sla_reset_trigger(self):
        """ Get the list of field for which we have to reset the SLAs (regenerate) """
        return ['team_id', 'priority', 'ticket_type_id', 'tag_ids', 'partner_id']

    def _sla_find_extra_domain(self):
        self.ensure_one()
        return [
            '|', '|', ('partner_ids', 'parent_of', self.partner_id.ids),
            ('partner_ids', 'child_of', self.partner_id.ids), ('partner_ids', '=', False)
        ]

    def _sla_generate_status_values(self, slas, keep_reached=False):
        """ Return the list of values for given SLA to be applied on current ticket """
        status_to_keep = dict.fromkeys(self.ids, list())

        # generate the map of status to keep by ticket only if requested
        if keep_reached:
            for ticket in self:
                for status in ticket.sla_status_ids:
                    if status.reached_datetime:
                        status_to_keep[ticket.id].append(status.sla_id.id)

        # create the list of value, and maybe exclude the existing ones
        result = []
        for ticket in self:
            for sla in slas:
                if not (keep_reached and sla.id in status_to_keep[ticket.id]):
                    result.append({
                        'ticket_id': ticket.id,
                        'sla_id': sla.id,
                        'reached_datetime': fields.Datetime.now() if ticket.stage_id == sla.stage_id else False
                        # in case of SLA on first stage
                    })

        return result

    def action_duplicate_tickets(self):
        for ticket in self.browse(self.env.context["active_ids"]):
            ticket.copy()

    def _prepare_ticket_number(self, values):
        seq = self.env["ir.sequence"]
        if "company_id" in values:
            seq = seq.with_company(values["company_id"])
        return seq.next_by_code("helpdesk.ticket.sequence") or "/"

    def _compute_access_url(self):
        res = super()._compute_access_url()
        for item in self:
            item.access_url = "/my/ticket/%s" % (item.id)
        return res

    # ---------------------------------------------------
    # Mail gateway
    # ---------------------------------------------------

    def _track_template(self, tracking):
        res = super()._track_template(tracking)
        ticket = self[0]
        if "stage_id" in tracking and ticket.stage_id.mail_template_id:
            res["stage_id"] = (
                ticket.stage_id.mail_template_id,
                {
                    # "auto_delete_message": True,
                    "subtype_id": self.env["ir.model.data"]._xmlid_to_res_id(
                        "mail.mt_note"
                    ),
                    "email_layout_xmlid": "mail.mail_notification_light",
                },
            )
        return res

    @api.model
    def message_new(self, msg, custom_values=None):
        """Override message_new from mail gateway so we can set correct
        default values.
        """
        if custom_values is None:
            custom_values = {}
        defaults = {
            "name": msg.get("subject") or _("No Subject"),
            "description": msg.get("body"),
            "partner_email": msg.get("from"),
            "partner_id": msg.get("author_id"),
        }
        defaults.update(custom_values)

        # Write default values coming from msg
        ticket = super().message_new(msg, custom_values=defaults)

        # Use mail gateway tools to search for partners to subscribe
        email_list = tools.email_split(
            (msg.get("to") or "") + "," + (msg.get("cc") or "")
        )
        partner_ids = [
            p.id
            for p in self.env["mail.thread"]._mail_find_partner_from_emails(
                email_list, records=ticket, force_create=False
            )
            if p
        ]
        ticket.message_subscribe(partner_ids)

        return ticket

    def message_update(self, msg, update_vals=None):
        """Override message_update to subscribe partners"""
        email_list = tools.email_split(
            (msg.get("to") or "") + "," + (msg.get("cc") or "")
        )
        partner_ids = [
            p.id
            for p in self.env["mail.thread"]._mail_find_partner_from_emails(
                email_list, records=self, force_create=False
            )
            if p
        ]
        self.message_subscribe(partner_ids)
        return super().message_update(msg, update_vals=update_vals)

    def _message_get_suggested_recipients(self):
        recipients = super()._message_get_suggested_recipients()
        try:
            for ticket in self:
                if ticket.partner_id:
                    ticket._message_add_suggested_recipient(
                        recipients, partner=ticket.partner_id, reason=_("Customer")
                    )
                elif ticket.partner_email:
                    ticket._message_add_suggested_recipient(
                        recipients,
                        email=ticket.partner_email,
                        reason=_("Customer Email"),
                    )
        except AccessError:
            # no read access rights -> just ignore suggested recipients because this
            # imply modifying followers
            return recipients
        return recipients
