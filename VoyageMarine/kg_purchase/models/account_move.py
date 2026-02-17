from ast import literal_eval

from odoo import models, fields, api,_
from odoo.exceptions import UserError, ValidationError
from odoo.tools import formatLang


class Partner(models.Model):
    _inherit = 'res.partner'

    is_outstanding = fields.Boolean(string="Invoice Has Outstanding", default=False)
    apply_credit_limit = fields.Boolean(string="Apply Credit Limit", default=False)


class AccountMove(models.Model):
    _inherit = 'account.move'

    vendor_id = fields.Many2one('res.partner',string="Vendor" , domain="[]")
    # show_commercial_partner_warning = fields.Char()
    # show_update_fpos = fields.Char()
    #
    # def action_update_fpos_values(self):
    #     print("action_update_fpos_values")
    picking_ids = fields.Many2many(
        'stock.picking',
        compute='_compute_picking_ids',
        string="GRN reference",

    )

    @api.depends(
        'line_ids.purchase_line_id.move_ids.state',
        'line_ids.purchase_line_id.move_ids.picking_id'
    )
    def _compute_picking_ids(self):
        for move in self:
            pickings = move.line_ids.mapped(
                'purchase_line_id.move_ids'
            ).filtered(
                lambda m: m.state == 'done' and m.picking_id
            ).mapped('picking_id')

            move.picking_ids = [(6, 0, pickings.ids)]

    def action_post(self):
        for move in self:
            if move.move_type == 'in_invoice':
                outstanding_bills = self.search([
                    ('partner_id', '=', move.partner_id.id),
                    ('move_type', '=', 'in_invoice'),
                    ('state', '=', 'posted'),
                    ('payment_state', 'in', ['not_paid', 'partial']),
                    ('invoice_date_due', '<', fields.Date.today())
                ])
                if outstanding_bills:
                    if not move.partner_id.is_outstanding:
                        move.partner_id.is_outstanding = True
                    account_team_ids = self.env['ir.config_parameter'].sudo().get_param('kg_purchase.account_team_ids')
                    if not account_team_ids:
                        raise UserError("Please add an account team user in settings.")
                    account_team_users = self.env['res.users'].browse(eval(account_team_ids))
                    for user in account_team_users:
                        if not user.partner_id.email:
                            raise UserError(f"The account team user {user.name} does not have an email address.")

                        body_html = f'''
                               <div>Dear {user.name},</div>
                               <p>The vendor <strong>{move.partner_id.name}</strong> has outstanding bills.</p>
                               <p>Please review these outstanding bills for timely settlement.</p>
                               <p>Best regards,</p>
                               <p>Your Accounts Team</p>
                               <div>{user.name}</div>
                           '''
                        email_values = {
                            'email_to': user.partner_id.email,
                            'email_from': self.env.user.email_formatted,
                            'subject': f"Outstanding Vendor Bill Notification for {move.partner_id.name}",
                            'body_html': body_html,
                        }
                        self.env['mail.mail'].create(email_values).send()

        return super(AccountMove, self).action_post()

    def js_assign_outstanding_line(self, line_id):
        result = super(AccountMove, self).js_assign_outstanding_line(line_id)
        if self.partner_id.debit >= 0:
            self.partner_id.is_outstanding = False

        return result


    @api.model
    def create(self, vals):
        invoice = super(AccountMove, self).create(vals)
        qtn_approve_users = self.env['ir.config_parameter'].sudo().get_param('kg_purchase.account_team_ids')
        if not qtn_approve_users or qtn_approve_users == '[]':
            raise ValidationError(_("Please Select Account Team Approval users in Configuration"))
        qtn_users = []
        qtn_approve_users_list = literal_eval(qtn_approve_users)

        for user_id in qtn_approve_users_list:
            user = self.env['res.users'].browse(user_id)
            if user:
                qtn_users.append(user)

        # if qtn_users:
        #     for user in qtn_users:
        #         note_1 = f"A new invoice has been created by {invoice.partner_id.name}."
        #         note_2 = (f"A new invoice has been created:\n\n"
        #                   f"Invoice Number: {invoice.name}\n"
        #                   f"Amount: {invoice.amount_total}\n"
        #                   "Please check the system for details.")
        #         invoice.activity_schedule(
        #             'kg_purchase.account_notification',
        #             user_id=user.id,
        #             note=note_1 if invoice.name else note_2
        #         )

        return invoice

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    ac_partner_id = fields.Many2one('res.partner',domain=[('state', '=', 'approval')])
    has_abnormal_deferred_dates = fields.Char()

    def _compute_partner_id(self):
        for line in self:
            line.partner_id = line.ac_partner_id