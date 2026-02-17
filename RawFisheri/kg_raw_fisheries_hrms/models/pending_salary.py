from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class PendingSalary(models.Model):
    _name = 'pending.salary'
    _description = 'Pending Salary'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Reference', default=lambda self: _('New'), readonly=True, copy=False)
    employee_id = fields.Many2one('hr.employee', string='Employee', tracking=True)
    settlement_date = fields.Date(string='Settlement Date', tracking=True)
    amount = fields.Float(string='Amount', tracking=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('approval_requested', 'Approval Requested'), ('approved', 'Approved'),
         ('rejected', 'Rejected'), ('cancel', 'Cancelled')], string="State", default='draft', copy=False, tracking=True)
    ps_approve_users_id = fields.Many2one("res.users", string="Pending Salary Approver", tracking=True)
    reason_for_reject = fields.Char(string="Reject Reason", copy=False)
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('pending.salary.sequence') or _('New')
        return super(PendingSalary, self).create(vals)

    def action_request_for_approval(self):
        if self.amount == 0.00:
            raise ValidationError(_("Please enter the amount !!"))
        if not self.ps_approve_users_id:
            raise ValidationError(_("Please select the user who will approve !!"))
        self.state = 'approval_requested'
        approver_id = self.ps_approve_users_id
        subject = _('Pending Salary Approval Request')
        label = 'Employee'
        date_label = 'Settlement Date'
        doc_type = "Pending Salary"
        amount = f"{'{:,.2f}'.format(self.amount)}"
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        approve_url = f"{base_url}/web/action_approve?id={self.id}"
        reject_url = f"{base_url}/web#action=kg_raw_fisheries_hrms.action_ps_reject_reason_wizard&active_id={self.id}"

        body = _(
            "<p>Dear {name},</p>"
            "<p>A {doc_type} is awaiting your approval.</p>"
            "<p><strong>{label}:</strong> {employee}<br/>"
            "<strong>Settlement Amount:</strong> {amount}<br/>"
            "<strong>{date_label}:</strong> {date}</p>"
            "<p>Best Regards,<br/>{requester}</p>"
        ).format(
            name=approver_id.name,
            doc_type=doc_type,
            label=label,
            employee=self.employee_id.name,
            amount=amount,
            date_label=date_label,
            date=self.settlement_date.strftime('%d/%m/%Y'),
            requester=self.create_uid.name
        )

        buttons = f"""
                    <div>
                        <a href="{approve_url}" style="padding:10px 15px;background:#28a745;color:#fff;text-decoration:none;border-radius:5px;font-weight:bold;">Approve</a>
                        <a href="{reject_url}" style="padding:10px 15px;background:#AF1740;color:#fff;text-decoration:none;border-radius:5px;font-weight:bold;">Reject</a>
                    </div>
                """

        self.env['mail.mail'].sudo().create({
            'subject': subject,
            'body_html': f"<html><body>{body}<br/>{buttons}</body></html>",
            'email_to': approver_id.email,
            'email_from': self.company_id.email,
        }).send()

    def action_approve(self):
        if self.env.user.id != self.ps_approve_users_id.id:
            raise UserError(_("You have no access to approve"))
        self.state = 'approved'

    def action_reject(self):
        return {
            'name': 'Reject Reason',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'ps.reject.reason.wizard',
            'target': 'new',
            'context': {'default_in_form': True}
        }

    def action_cancel(self):
        self.state = 'cancel'

    @api.ondelete(at_uninstall=False)
    def _unlink_except_draft(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_("You can delete only records in the draft state."))

    def action_draft(self):
        self.state = 'draft'
        self.reason_for_reject = False
