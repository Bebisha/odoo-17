# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, tools

# to use in your custom models
_APPROVAL_STATES = [
    ('draft', 'Draft'),
    ('request', 'Pending Approval'),
    ('approve', 'Approved'),
    ('reject', 'Rejected'),
]


class ApprovalMixin(models.AbstractModel):
    _name = 'approval.mixin'
    _description = 'Approval Mixin'

    def _get_default_approval_template(self):
        template_id = self.env['approval.template'].search([('res_model_name', '=', self._name)], limit=1)
        return template_id

    approvals = fields.Json()
    approval_id = fields.Many2one('approval.template', string='Approval', default=_get_default_approval_template)
    is_done = fields.Boolean(compute='_compute_is_done')

    def _valid_field_parameter(self, field, name):
        # If the field has `is_approval_state` we consider it as the approval status field
        return name == 'is_approval_state' or super()._valid_field_parameter(field, name)

    @tools.ormcache('self.env.uid', 'self.env.su')
    def _get_approval_field(self):
        """Returns all fields having the parameter is_approval_state=True"""

        approval_fields = [name for name, field in self._fields.items() if getattr(field, 'is_approval_state', None)]
        return approval_fields[0] if approval_fields else approval_fields

    def _compute_is_done(self):
        """Check whether the approval reached the last one or not"""

        for rec in self:
            print('>>>>>>>>>>', rec.approvals)
            rec.is_done = rec.approval_id.is_done(rec.approvals)

    def show_approval_buttons(self):
        """Check whether the current user can see the approval/reject button"""
        user = self.env.user.id
        approval_dict = self.approvals and self.approvals.get('next_approval')
        approval_lines = []
        if approval_dict:
            for item in approval_dict:
                if item.get('approval_line_id'):
                    approval_lines.append(item['approval_line_id'])
        print("approval_lines--->>", approval_lines)
        if approval_lines:
            line_ids = self.env['approval.template.line'].browse(approval_lines)
            if len(line_ids.group_ids) > 0:
                groups = line_ids.group_ids
                approval_users = groups.mapped('users')
            else:
                approval_users = line_ids.mapped('user_ids')
            if user in approval_users.ids:
                return True
        return False

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = dict(default or {})
        if 'approvals' in default:
            default['approvals'] = {}
        return super(ApprovalMixin, self).copy(default=default)

    def write(self, vals):
        if 'approvals' in vals and not self._get_approval_field():
            vals['approvals'] = {}
        return super(ApprovalMixin, self).write(vals)

    def _update_approval_state(self, field_value, approval_vals=None):
        field_name = self._get_approval_field()
        print(approval_vals, "FIELDDDD", field_value)
        if field_name:
            vals = {
                field_name: field_value
            }
            if isinstance(approval_vals, dict):
                vals.update({
                    'approvals': approval_vals
                })
            self.write(vals)

    def _do_reject(self):
        self = self.with_context(active_id=self.id, active_model=self._name)
        approval_vals = self.approval_id.reject(self.approvals)
        self._update_approval_state('reject', approval_vals)

    def request(self):
        """Use this method to request for approval. The approval structure builds at this point"""

        self = self.with_context(active_id=self.id, active_model=self._name)
        print(self, "SSSSS")
        approval_vals = self.approval_id.init_approval_structure()
        print(approval_vals, "APPORRR")
        self._update_approval_state('request', approval_vals)

    def approve(self):
        """Use this method to approve the request at any point"""

        self_su = self.with_context(active_id=self.id, active_model=self._name)
        approval_vals = self_su.approval_id.approve(self_su.approvals)
        print(approval_vals, "1")
        self_su.approvals = approval_vals
        if hasattr(self_su, 'message_mail_with_source'):
            self_su.message_mail_with_source(
                "web_approval.approval_summary",
                render_values={},
            )
        if self_su.is_done:
            for data in self_su:
                data.activity_schedule('web_approval.mail_activity_approval_purchase', user_id=self.env.user.id,
                                       note=f'Order {data.name} has been approved .').action_feedback()
            self_su._update_approval_state('approve')

    def reject(self):
        """Use this method to reject the request at any point. This method must be returned from the method
        it is being called as sometimes this it returns a view action"""

        self.ensure_one()
        self = self.with_context(active_id=self.id, active_model=self._name)
        if self.approval_id.rejection_comment_required:
            action = self.env["ir.actions.actions"]._for_xml_id("web_approval.action_approval_comment")
            action['name'] = _("Reject Reason")
            return action
        else:
            context = self._context
            activity_type = self.env.ref('web_approval.mail_activity_approval')
            model = context.get('active_model')
            rec_id = context.get('active_id')
            record_id = self.env[model].browse(rec_id)
            activitie = self.env['mail.activity'].search(
                [('activity_type_id', '=', activity_type.id), ('res_model', '=', model), ('res_id', '=', record_id.id)])
            for act in activitie:
                act.unlink()
            self._do_reject()

    def reset(self):
        """Use this method to clear all previous approvals"""

        self = self.with_context(active_id=self.id, active_model=self._name)
        approval_vals = self.approval_id.clear_previous_approvals()
        self._update_approval_state('draft', approval_vals)
        # unlink all activities related to this record
        activities = self.env['mail.activity'].search(
            [('res_model', '=', self._name), ('activity_type_id.category', '=', 'approval')])
        activities.unlink()
