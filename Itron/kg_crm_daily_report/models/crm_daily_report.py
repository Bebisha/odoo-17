from datetime import datetime, date
from odoo.exceptions import UserError, ValidationError

from odoo import fields, models, api, _
from babel.dates import format_date


class CRMDailyReport(models.Model):
    _name = 'crm.daily.report'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    @api.model
    def _default_employee(self):
        return self.env.user.id

    @api.model
    def _default_report_lines(self):
        return [
            (0, 0, {'name': 'Call'}),
            (0, 0, {'name': 'Email'}),
            (0, 0, {'name': 'Followups'}),
            (0, 0, {'name': 'New Leads'}),
            (0, 0, {'name': 'Meetings'}),
            (0, 0, {'name': 'Demos'}),
            (0, 0, {'name': 'Proposals'}),
            (0, 0, {'name': 'Negotiation'}),
            (0, 0, {'name': 'Order Confirmation'}),
            (0, 0, {'name': 'Kick-Off'}),
            (0, 0, {'name': 'No.of Contacts Identified for Cold Calls'}),
            (0, 0, {'name': "Next day's plan"}),

        ]

    name = fields.Char('Name', required=True, default='Daily Report')
    date = fields.Date('Date', required=True, default=lambda self: (date.today()))
    user_id = fields.Many2one('res.users', string="Employee", required=True, default=_default_employee, )
    report_line_ids = fields.One2many('crm.daily.report.lines', 'daily_report_id', string="Lines",
                                      default=_default_report_lines)
    daily_update_line_ids = fields.One2many('daily.update.line', 'daily_report_id', string="Daily Update")
    notes = fields.Html('No.of Other Notes')
    no_cold_calls = fields.Integer('No.of Contacts Identified for Cold Calls : ')
    lead_statistics = fields.Html('Lead Statistics', compute="compute_lead_statistics")
    status = fields.Selection([('draft', 'Draft'), ('sent', 'Sent')], default="draft", required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    lead_activity_ids = fields.Many2many('mail.activity', string='Lead Activities')

    def view_lead_activities(self):
        crm_activities = self.env['mail.activity'].search(
            [('active', 'in', [True, False]), ('res_model', '=', 'crm.lead'), ('user_id', '=', self.user_id.id),
             ('date_deadline', '=', self.date)])

        return {
            'name': _('Scheduled Activities'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'mail.activity',
            'domain': [('id', 'in', crm_activities.ids), ('active', 'in', [True, False])],
            'context': "{'create': False}"
        }

    @api.depends('user_id', 'date', 'lead_activity_ids')
    @api.onchange('user_id', 'date', 'lead_activity_ids')
    def compute_activity_count(self):
        for rec in self:
            # activity_leads = self.env['crm.lead'].search([('activity_user_id', '=', rec.user_id.id), ('activity_date_deadline', '=', rec.date)])
            # activites = activity_leads.mapped('activity_ids').filtered(lambda x: x.date_deadline == rec.date and x.active in [True, False])
            crm_activities = self.env['mail.activity'].search(
                [('active', 'in', [True, False]), ('res_model', '=', 'crm.lead'), ('user_id', '=', rec.user_id.id),
                 ('date_deadline', '=', rec.date)])
            rec.lead_activity_ids = [(6, 0, crm_activities.ids)]
            call_count = 0
            email_count = 0
            followup_count = 0
            meet_count = 0
            demo_count = 0
            proposal_count = 0
            order_count = 0
            kick_count = 0
            for act in crm_activities:
                if act.activity_type_id.lead_activities == 'call':
                    call_count += 1
                elif act.activity_type_id.lead_activities == 'email':
                    email_count += 1
                elif act.activity_type_id.lead_activities == 'followups':
                    followup_count += 1
                elif act.activity_type_id.lead_activities == 'meetings':
                    meet_count += 1
                elif act.activity_type_id.lead_activities == 'demos':
                    demo_count += 1
                elif act.activity_type_id.lead_activities == 'proposals':
                    proposal_count += 1
                elif act.activity_type_id.lead_activities == 'order_confirmation':
                    order_count += 1
                elif act.activity_type_id.lead_activities == 'kick_off':
                    kick_count += 1

            for line in rec.report_line_ids:
                if line.name == 'Call':
                    line.count = call_count
                elif line.name == 'Email':
                    line.count = email_count
                elif line.name == 'Followups':
                    line.count = followup_count
                elif line.name == 'Meetings':
                    line.count = meet_count
                elif line.name == 'Demos':
                    line.count = demo_count
                elif line.name == 'Proposals':
                    line.count = proposal_count
                elif line.name == 'Order Confirmation':
                    line.count = order_count
                elif line.name == 'Kick-Off':
                    line.count = kick_count
                elif line.name == 'New Leads':
                    new_lead = self.env['crm.lead'].search([('user_id', '=', rec.user_id.id)]).filtered(
                        lambda x: x.date_added.date() == rec.date)
                    line.count = len(new_lead)

    def compute_lead_statistics(self):
        for record in self:
            user_leads = self.env['crm.lead'].search([('user_id', '=', record.user_id.id),('type', '=', 'opportunity')])
            stages = self.env['crm.stage'].search([('name', 'not in', ['Lost', 'Won', 'Park'])])
            total_count = 0
            html_cont = """<table border="1" cellpadding="1" cellspacing="0" style="border-collapse: collapse; width: 35%;">
                            <thead>
                                <tr>
                                    <th>Stage</th>
                                    <th style="text-align:center;">Count</th>
                                </tr>
                            </thead>
                            <tbody>"""
            for s in stages:
                stage_leads = user_leads.filtered(lambda x: x.stage_id.id == s.id and x.user_id.id == record.user_id.id)
                total_count += len(stage_leads)
                html_cont += f"""
                                <tr>
                                    <td>{s.name}</td>
                                    <td style="text-align:center;">{len(stage_leads)}</td>
                                </tr>
                            """
            html_cont += f"""</tbody>
                </table>
                <br/>
                <b>Total Leads : {total_count}</b>
                <br/>"""
            record.lead_statistics = html_cont

    @api.onchange('date', 'user_id')
    def onchange_date(self):
        if self.date:
            date_in_words = format_date(date=self.date, format='d MMMM y', locale='en')
            self.name = str(self.user_id.name) + ' : Daily Report for ' + str(date_in_words)

    def action_send_report(self):
        approval_ids = self.env.company.daily_report_manager_ids
        group_send_mail = []

        for config_rec in approval_ids:
            if config_rec.email:
                group_send_mail.append(config_rec.email)

        date_in_words = format_date(date=self.date, format='d MMMM y', locale='en')

        html_content = f"""
            <p>Dear Team,</p>
            <p>Please find below the daily report for {date_in_words}:</p>
            <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 85%;">
                <thead>
                    <tr>
                        <th>Action</th>
                        <th style="text-align:center;">Count</th>
                        <th>Description</th>
                        <th>Next Activity</th>
                    </tr>
                </thead>
                <tbody>
        """
        for line in self.report_line_ids:
            description = line.description.replace('\n', '<br>') if line.description else ''
            next_activity = line.next_activity.replace('\n', '<br>') if line.next_activity else ''
            html_content += f"""
                <tr>
                    <td>{line.name}</td>
                    <td style="text-align:center;">{line.count if line.count else ''}</td>
                    <td>{description}</td>
                    <td>{next_activity}</td>
                </tr>
            """
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        redirect_url = "{}/web#id={}&view_type=form&model={}".format(base_url, self.id, self._name)

        html_content += """
                                </tbody>
                            </table>
                            <br/>                            
                            <b>LEAD STATISTICS</b><br/>

                            <table border="1" cellpadding="1" cellspacing="0" style="border-collapse: collapse; width: 35%;">
                        <thead>
                            <tr>
                                <th>Stage</th>
                                <th style="text-align:center;">Count</th>
                            </tr>
                        </thead>
                        <tbody>


                        """

        user_leads = self.env['crm.lead'].sudo().search([('user_id', '=', self.user_id.id),('type', '=', 'opportunity')])
        stages = self.env['crm.stage'].search([('name', 'not in', ['Lost', 'Won', 'Park'])])
        total_count = 0
        for s in stages:
            stage_leads = user_leads.filtered(lambda x: x.stage_id.id == s.id)
            total_count += len(stage_leads)
            html_content += f"""
                            <tr>
                                <td>{s.name}</td>
                                <td style="text-align:center;">{len(stage_leads)}</td>
                            </tr>
                        """

        html_content += """
            </tbody>
            </table>
            <br/>
            <b>Total Leads : """ + str(total_count) + """</b>
            <br/>
            <br/>
            <div>
                <a href=""" + redirect_url + """>
                    <button style='padding:7px;background-color:#71639e;color:white;height:35px;border-radius:10px;'>
                        VIEW REPORT
                    </button>
                </a>
            </div>
            <br/>
            <br/>
            <p>Best regards,<br>
            """ + self.user_id.name + """<br></p>
        """
        mail_values = {
            'subject': self.name,
            'email_to': self.user_id.email,
            'email_cc': ', '.join(group_send_mail),
            'body_html': html_content,
            'email_from': 'itron@klystronglobal.com',
        }

        mail = self.env['mail.mail'].sudo().create(mail_values)
        mail.send()
        self.status = 'sent'

    def reset_draft(self):
        self.status = 'draft'


class CRMDailyReportLines(models.Model):
    _name = 'crm.daily.report.lines'

    daily_report_id = fields.Many2one('crm.daily.report')
    name = fields.Char('Action', required=True)
    count = fields.Integer('Count')
    description = fields.Text('Description')
    next_activity = fields.Text('Next Activity')

class DailyUpdateLine(models.Model):
    _name = 'daily.update.line'

    daily_report_id = fields.Many2one('crm.daily.report')
    progress_updates = fields.Text('Progress Updates')
    action_items = fields.Text('Action Items')
    road_blocks = fields.Text('Roadblocks')
