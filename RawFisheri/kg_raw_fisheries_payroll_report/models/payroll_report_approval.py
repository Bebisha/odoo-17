# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class PayrollReportApproval(models.Model):
    _name = 'payroll.report.approval'
    _description = 'payroll.report.approval'

    name = fields.Char(sring='Reference')
    state = fields.Selection([('draft', "Draft"), ('approval_requested', "Approval Requested"), ('approved', "Approved")], string="State", default='draft')
    date_from = fields.Date(string='From')
    date_to = fields.Date(string='To')
    attachment_id = fields.Many2one('ir.attachment', ondelete='cascade', auto_join=True, copy=False)
    employee_site = fields.Selection([("crew", "Crew"), ("hq", "HQ")], string='Site', default="hq")
    vessel_id = fields.Many2one('sponsor.sponsor', string="Vessel")
    datas = fields.Binary(string='Attachment', related='attachment_id.datas')

    @api.model
    def create(self, vals):
        """ Payroll report approval sequence number generation """
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'payroll.report.approval.sequence') or _('New')
        return super(PayrollReportApproval, self).create(vals)

    def action_request(self):
        """ Action for Requesting Approval """
        for rec in self:
            participant_ids = [user.partner_id.id for user in
                               self.env['res.users'].search(
                                   [('groups_id', 'in', self.env.ref('kg_raw_fisheries_payroll_report.payroll_report_approver').id)])]

            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            record_url = f"{base_url}/web#id={rec.id}&model={rec._name}&view_type=form"

            message = self.env['mail.message'].create({
                'model': rec._name,
                'res_id': rec.id,
                'subject': 'Payroll Report Approval Request',
                'body': '''
                    <html>
                    Payroll Report Approval Request<br/>
                    <b>{rec_name}</b> has been submitted by: 
                    <b style="text-transform: uppercase">{user_name}</b>.<br/>
                    Please verify and confirm the same.<br/>
                    <a href="{url}" style="display: inline-block; padding: 10px 20px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">
                        View
                    </a>
                    </html>
                '''.format(rec_name=rec.name, user_name=self.env.user.partner_id.name, url=record_url),
                'author_id': self.env.user.partner_id.id,
            })
            self.env['mail.thread'].message_notify(
                partner_ids=participant_ids,
                body=message.body,
                subject=message.subject,
                record_name=self.name,
                model_description=self._description,
                force_send=True,
            )

            rec.write({
                'state': 'approval_requested'
            })

    def action_approve(self):
        """ Action for Payroll Report Approval """
        for rec in self:
            rec.write({
                'state': 'approved'
            })