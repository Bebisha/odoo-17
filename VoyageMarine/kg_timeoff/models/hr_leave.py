from ast import literal_eval

from odoo import fields, models,_,api
from odoo.exceptions import ValidationError, UserError


class HrTimeoffInherit(models.Model):
    _inherit = 'hr.leave'

    requested_by = fields.Many2one("res.users", string="Requested By")
    approved_by = fields.Many2one("res.users", string="Approved by")
    is_request = fields.Boolean(string="Is Request", default=False, copy=False)
    is_gm_approve = fields.Boolean(string="Is General Manager Approve", default=False, copy=False)
    is_rfq_approve = fields.Boolean(string="Is RFQ Approve", default=False, copy=False)
    is_reject = fields.Boolean(string="Is Reject", default=False, copy=False)


    @api.model
    def create(self, vals):
        vals['is_request'] = True
        return super(HrTimeoffInherit, self).create(vals)

    # @api.model
    # def action_approve(self):
    #     for record in self:
    #         record.is_request = True
    #     return super(HrTimeoffInherit,self).action_approve()



    def action_refuse(self):
        self.is_reject = True
        self.is_request = False
        self.is_gm_approve = False
        self.is_rfq_approve = False
        return super(HrTimeoffInherit, self).action_refuse()

    def kg_gm_approve(self):
        # Retrieve the parameter
        gm_approve_users = self.env['ir.config_parameter'].sudo().get_param(
            'kg_timeoff.general_manager_ids', '[]')  # Default to '[]' if not found

        # Validate the parameter format
        try:
            gm_approve_users_list = literal_eval(gm_approve_users)
            if not isinstance(gm_approve_users_list, list):
                raise ValueError("gm_approve_users is not a list")
        except (ValueError, SyntaxError) as e:
            raise UserError(_("Invalid configuration for General Manager IDs: %s") % str(e))

        if not gm_approve_users_list:
            raise UserError(_("Choose a Time off approver"))

        if self.env.user.id not in gm_approve_users_list:
            raise UserError(_("You have no access to approve"))
        gm_users = []
        general_manager_notification_activity = self.env.ref(
            'kg_timeoff.general_manager_approval_notification')
        activity_1 = self.activity_ids.filtered(
            lambda l: l.activity_type_id == general_manager_notification_activity)
        not_current_user_confirm = activity_1.filtered(lambda l: l.user_id != self.env.user)


        for ccc in not_current_user_confirm:
            ccc.unlink()

        activity_2 = self.activity_ids.filtered(
            lambda l: l.activity_type_id == general_manager_notification_activity)
        activity_2.action_done()

        for user_id in gm_approve_users_list:
            user = self.env['res.users'].browse(user_id)
            if user:
                gm_users.append(user)

        self.approved_by = self.env.user.id
        self.is_rfq_approve = True
        self.is_gm_approve = True
        self.message_post(body=_("GM approval is created for time off"))

    def kg_gm_reject(self):
        gm_approve_users = self.env['ir.config_parameter'].sudo().get_param(
            'kg_timeoff.general_manager_ids', '[]')  # Default to '[]' if not found

        try:
            gm_approve_users_list = literal_eval(gm_approve_users)
            if not isinstance(gm_approve_users_list, list):
                raise ValueError("gm_approve_users is not a list")
        except (ValueError, SyntaxError) as e:
            raise UserError(_("Invalid configuration for General Manager IDs: %s") % str(e))

        if not gm_approve_users_list:
            raise UserError(_("Choose a Time off approver"))

        if self.env.user.id not in gm_approve_users_list:
            raise UserError(_("You have no access to reject"))
        else:
            self.action_refuse()
            self.state = 'refuse'
            self.is_reject = True
            self.is_request = False
            self.is_gm_approve = False
            self.is_rfq_approve = False

    def action_draft(self):
        res = super(HrTimeoffInherit, self).action_draft()
        self.is_reject = False
        self.is_request = True
        self.is_gm_approve = False
        self.is_rfq_approve = False
        self.requested_by = False
        self.approved_by = False
        # self.forms_created = False
        return res


    # def action_validate(self):
    #     for rec in self:
    #         if rec.is_reject:
    #             raise ValidationError(_("You cannot confirm because your request has been rejected"))
    #
    #         if not rec.is_gm_approve:
    #             raise ValidationError(_("You cannot do this action without approval"))
    #         return super(HrTimeoffInherit, self).action_validate()
