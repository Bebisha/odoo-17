from datetime import datetime
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from collections import defaultdict


class Lead(models.Model):
    _inherit = 'crm.lead'

    activity_1_id = fields.Many2one('kg.activity', 'Activity')
    date_1 = fields.Date('Date By')
    activity_2_id = fields.Many2one('kg.activity', 'Activity')
    date_2 = fields.Date('Date By')
    activity_3_id = fields.Many2one('kg.activity', 'Activity')
    date_3 = fields.Date('Date By')
    activity_4_id = fields.Many2one('kg.activity', 'Activity')
    date_4 = fields.Date('Date By')
    activity_5_id = fields.Many2one('kg.activity', 'Activity')
    date_5 = fields.Date('Date By')

    deal_milestone_ids = fields.One2many('kg.deal.milestone', 'lead_id')

    date_added = fields.Datetime('Date Added', default=lambda self: fields.Datetime.now())
    demo_by = fields.Date('Demo By')
    proposed_by = fields.Date('Proposed Date')
    closure_by = fields.Date('Closure By')
    quarter_by = fields.Selection([('q1', 'Q1'), ('q2', 'Q2'), ('q3', 'Q3'), ('q4', 'Q4')], default='q1',
                                  string='Quarter By')
    proposed = fields.Boolean(related="stage_id.is_proposed")
    activity_status_id = fields.Many2one('lead.activity.status', string="Activity Status")

    @api.constrains('stage_id')
    def onchange_stage_id(self):
        """ UserError for Proposed Date for Leads """
        for lead in self:
            if lead.proposed:
                if not lead.proposed_by:
                    raise UserError("Please Enter Proposed Date!")

    @api.model
    def year_selection(self):
        year = 2010
        year_list = []
        while year != 3000:
            year_list.append((str(year), str(year)))
            year += 1
        return year_list

    year = fields.Selection(year_selection, string="Year", default=str(datetime.now().year))

    qualification_disqualification = fields.Many2many('kg.qualifications', string='Qualification/Disqualification')

    demo_who_id = fields.Many2one('res.users', string='Who?')
    proposed_who_id = fields.Many2one('res.users', string='Who?')
    closure_who_id = fields.Many2one('res.users', string='Who?')
    quarter_who_id = fields.Many2one('res.users', string='Who?')

    dm = fields.Char('Decision Maker')
    contact_dm = fields.Char('Contact')
    key_instructor = fields.Char('Key Instructor')
    key_influencer = fields.Char('Key Influencer')
    contact_key_instructor = fields.Char('Contact')
    gate_keeper = fields.Char('Gate Keeper')
    contact_gate_keeper = fields.Char('Contact')

    pain_points = fields.Text('Pain Points')
    modules = fields.Many2many('crm.modules', string='Modules')
    direct = fields.Boolean("Direct", copy=False)
    partner_ref = fields.Char("Partner/Reference", copy=False)
    next_action = fields.Char("Next Action", copy=False)
    next_action_date = fields.Date("Next Action Date")
    given_demo = fields.Boolean("Demo Given")
    sent_proposal = fields.Boolean("Sent Proposal")
    estimation_count = fields.Integer(string='Estimations', compute='_compute_estimation_count')
    kg_crm_estimation_ids = fields.One2many('kg.crm.estimation', 'lead_id', string='Estimations')
    lead_interest_id = fields.Many2one('lead.interest', 'Lead Interest', ondelete='cascade', copy=False)
    gate_keeper_id = fields.Many2one('res.partner', 'Gate Keeper')
    country = fields.Char('Country')

    company_id = fields.Many2one(
        'res.company', string='Company', index=True,
        default=lambda self: self.env.company.id, readonly=False, store=True)

    @api.depends('kg_crm_estimation_ids')
    def _compute_estimation_count(self):
        for lead in self:
            lead.estimation_count = self.env['kg.crm.estimation'].search_count([('lead_id', '=', lead.id)])

    def action_view_estimations(self):
        self.ensure_one()
        return {
            'name': ('Estimations'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'kg.crm.estimation',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('lead_id', '=', self.id)],
        }

    def update_step_no(self):
        count = 0
        for rec in self.deal_milestone_ids.sorted(key=lambda r: r.id):
            count += 1
            rec.name = 'Step ' + str(count)

    def create_estimation(self):
        self.ensure_one()
        if not self.partner_id:
            raise UserError("Please add a customer first.")

        estimation = self.env['kg.crm.estimation'].create({
            'name': self.name,
            'customer_id': self.partner_id.id,
            'lead_id': self.id,
        })

        for module in self.modules:
            self.env['kg.crm.estimation.line'].create({
                'estimation_id': estimation.id,
                'item_id': module.product_id.id,
            })

        return {
            'name': 'Create Estimation',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'kg.crm.estimation',
            'res_id': estimation.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def write(self, vals):

        result = super(Lead, self).write(vals)

        # Stage change validations - check per record
        if "stage_id" in vals:
            stage = self.env["crm.stage"].browse(vals["stage_id"])
            if stage.is_qualified:
                for rec in self:
                    if rec.expected_revenue == 0:
                        raise UserError("Please add the budget or expected revenue !")
                    if not rec.lead_interest_id:
                        raise UserError("Lead interest is missing !")
                    if not rec.gate_keeper_id:
                        raise UserError("Update Gate Keeper info !")
                    if not rec.source_id:
                        raise UserError("Update the Lead Source !")
                    if not rec.date_deadline:
                        raise UserError("Update expected closing date !")

        return result

    @api.model
    def create(self, vals):

        rec = super(Lead, self).create(vals)

        if rec.country and not rec.country_id:
            country_id = self._get_country_id_from_str(rec.country)
            print(country_id,'country_idcountry_id')
            if country_id:
                rec.country_id = country_id
                companies = rec.env['res.company'].sudo().search([])
                target_company = companies.filtered(lambda c: c.country_id == rec.country_id)
                if not target_company:
                    target_company = rec.env['res.company'].sudo().search([
                        ('country_code', '=', 'AE')
                    ], limit=1)
                rec.company_id = target_company or rec.env.company

        if rec.email_from:
            template = self.env.ref('kg_crm.email_template_lead_welcome', raise_if_not_found=False)
            if template:
                template.send_mail(
                    rec.id,
                    force_send=True,
                    email_layout_xmlid='mail.mail_notification_layout_with_responsible_signature'
                )

        return rec

    # @api.onchange('company_id')
    # def onchange_company_id(self):
    #     """ Auto-assign a team only when company_id changes """
    #     for rec in self:
    #         if rec.company_id:
    #             team = self.env['crm.team'].sudo().search([
    #                 ('company_id', '=', rec.company_id.id),
    #                 ('active', '=', True)
    #             ], limit=1)
    #             rec.team_id = team.id if team else False

    @api.depends('company_id')
    def _compute_team_id(self):
        """ Override default team assignment to always match company_id """
        super(Lead, self)._compute_team_id()
        for rec in self:
            if rec.company_id:
                team = self.env['crm.team'].sudo().search([
                    ('company_id', '=', rec.company_id.id),
                    ('active', '=', True)
                ], limit=1)
                rec.team_id = team.id if team else False

    # @api.onchange('country_id')
    # def _compute_company_id_custom(self):
    #     """ Compute company_id based on fb medium + country """
    #     for rec in self:
    #         if rec.country_id:
    #             companies = rec.env['res.company'].sudo().search([])
    #             target_company = companies.filtered(lambda c: c.country_id == rec.country_id)
    #             if not target_company:
    #                 target_company = rec.env['res.company'].sudo().search([
    #                     ('country_code', '=', 'AE')
    #                 ], limit=1)
    #             rec.company_id = target_company or rec.env.company
    #         else:
    #             rec.company_id = rec.env.company

    def _get_country_id_from_str(self, country_str):
        country_str = (country_str or "").strip()
        country_code = country_str.upper()
        country = self.env['res.country'].sudo().search([('code', '=', country_code)], limit=1)

        if not country:
            country_name = country_str.title()
            country = self.env['res.country'].search([('name', 'ilike', country_name)], limit=1)

        return country.id if country else False

    def _prepare_grouped_data(self):
        Lead = self.env['crm.lead']
        Country = self.env['res.country']

        today = fields.Date.today()
        leads = Lead.search([('type', '=', 'lead'), ('active', '=', True)])
        if not leads:
            return None, None, None

        grouped_data = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        all_interests = set()
        interest_status_map = defaultdict(set)

        for lead in leads:
            lead_country_name = (lead.country or "").strip()

            if lead_country_name:
                country_rec = None

                if len(lead_country_name) == 2:
                    country_rec = Country.search([('code', '=', lead_country_name.upper())], limit=1)
                    print("Matched Country by CODE:", country_rec.name if country_rec else "None")

                if not country_rec:
                    country_rec = Country.search([('name', '=ilike', lead_country_name)], limit=1)

                if not country_rec:
                    print(lead_country_name, 'lead_country_name')

                    country_rec = Country.search([('name', 'ilike', lead_country_name)], limit=1)
                    print(country_rec, 'country_rec')

                country_name = country_rec.name if country_rec else lead_country_name
            else:
                country_name = "No Country"


            interest = lead.lead_interest_id.name if lead.lead_interest_id else "None"
            all_interests.add(interest)

            status = lead.activity_status_id.name if lead.activity_status_id else "None"
            interest_status_map[interest].add(status)

            grouped_data[country_name][interest][status] += 1

        sorted_grouped_data = {k: grouped_data[k] for k in sorted(grouped_data, key=lambda x: (x == "No Country", x))}
        return sorted_grouped_data, sorted(all_interests, key=lambda x: (x == "None", x)), interest_status_map

    def _generate_leads_html_table(self, grouped_data, interests, interest_status_map):
        html = []
        html.append(
            '<table border="1" cellspacing="0" cellpadding="4" style="border-collapse:collapse; font-family:Arial; font-size:13px; text-align:center;">'
        )

        # First header row
        html.append('<thead>')
        html.append('<tr style="background-color:#f2f2f2; font-weight:bold;">')
        html.append('<th rowspan="2" style="padding:6px; text-align:left;">Country</th>')  # Left align Country header
        for interest in interests:
            statuses = sorted(interest_status_map[interest], key=lambda x: (x == "None", x))
            html.append(f'<th colspan="{len(statuses)}" style="padding:6px;">{interest}</th>')
        html.append('<th rowspan="2" style="padding:6px;">Total</th>')
        html.append('</tr>')

        # Second header row
        html.append('<tr style="background-color:#f9f9f9; font-weight:bold;">')
        for interest in interests:
            for status in sorted(interest_status_map[interest], key=lambda x: (x == "None", x)):
                html.append(f'<th style="padding:6px;">{status}</th>')
        html.append('</tr>')
        html.append('</thead>')

        # Body rows
        html.append('<tbody>')
        col_totals = defaultdict(int)
        grand_total = 0

        for country, interests_dict in grouped_data.items():
            row_total = 0
            html.append(
                f'<tr><td style="font-weight:bold; text-align:left;">{country}</td>')  # Left align Country values
            for interest in interests:
                for status in sorted(interest_status_map[interest], key=lambda x: (x == "None", x)):
                    count = interests_dict.get(interest, {}).get(status, 0)
                    html.append(f'<td>{count if count else ""}</td>')
                    col_totals[(interest, status)] += count
                    row_total += count
            html.append(f'<td style="font-weight:bold;">{row_total}</td></tr>')
            grand_total += row_total

        # Totals row
        html.append('<tr style="background-color:#e6e6e6; font-weight:bold;">')
        html.append('<td style="text-align:left;">Total</td>')  # Left align Total label in footer
        for interest in interests:
            for status in sorted(interest_status_map[interest], key=lambda x: (x == "None", x)):
                html.append(f'<td>{col_totals[(interest, status)]}</td>')
        html.append(f'<td>{grand_total}</td>')
        html.append('</tr>')

        html.append('</tbody></table>')
        return ''.join(html)

    def action_send_daily_lead_report(self):
        grouped_data, interests, interest_status_map = self._prepare_grouped_data()
        if not grouped_data:
            return
        table_html = self._generate_leads_html_table(grouped_data, interests, interest_status_map)
        param_obj = self.env['ir.config_parameter'].sudo()
        crm_daily_mail_users_ids_str = param_obj.get_param('crm_daily_mail_users_ids', default='')
        crm_daily_mail_users_ids = [int(id.strip()) for id in crm_daily_mail_users_ids_str.strip('[]').split(',') if
                                    id.strip()]

        if not crm_daily_mail_users_ids:
            return

        email_recipients = self.env['res.users'].browse(crm_daily_mail_users_ids).mapped('email')
        email_to = ",".join(filter(None, email_recipients))

        if not email_to:
            return

        today_str = datetime.today().strftime("%-d %b %Y (%A)")
        today_sub_str = datetime.today().strftime("%-d %b %Y ")

        body_html = f"""
        <div style="font-family:Arial; font-size:14px;">
            <p>Dear Team,</p>
            <p>Please find below the country-wise daily lead report for <strong>{today_str}</strong>.</p>
            {table_html}
            <p>Best regards,<br/>Klystron Global</p>
        </div>
        """

        self.env['mail.mail'].create({
            'subject': f"Daily Lead Report – {today_sub_str}",
            'body_html': body_html,
            'email_to': email_to,
        }).send()

class KgQualifications(models.Model):
    _name = 'kg.qualifications'

    name = fields.Char('Name')


class KGCRMStage(models.Model):
    _inherit = "crm.stage"

    is_qualified = fields.Boolean('Is Qualified?', copy=False)
    is_discovery = fields.Boolean('Is Discovery?', copy=False)
    is_proposed = fields.Boolean('Is Proposed Stage?', copy=False)
    is_proposal_cold = fields.Boolean('Is Proposal Cold?', copy=False)
    is_negotiation = fields.Boolean('Is Negotiation?', copy=False)
    is_po_waiting = fields.Boolean('Is PO Waiting?', copy=False)


class Lead2OpportunityPartner(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner'

    def action_apply(self):
        if self.name == 'merge':
            result_opportunity = self._action_merge()
        else:
            result_opportunity = self._action_convert()

        qualified_stage_id = self.env['crm.stage'].search([('is_qualified', '=', True)], limit=1).id
        result_opportunity.sudo().write({'stage_id': qualified_stage_id})
        return result_opportunity.redirect_lead_opportunity_view()
