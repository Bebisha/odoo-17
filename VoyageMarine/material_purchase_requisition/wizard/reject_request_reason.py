
from odoo import api, fields, models, _
from odoo.exceptions import UserError



class RejectedReasonWizard(models.TransientModel):
    _name = 'rejection.reason.wizard'
    _description = 'Rejection Reason Wizard'

    rejection_reason = fields.Text(string="Rejection Reason")
    mr_id = fields.Many2one("material.purchase.requisition", string="Material Reference")
    is_reject = fields.Boolean(default=False, string="Is Reject")

    def action_reject_button(self):
        active_id = self.env.context.get('active_id')
        mr = self.env['material.purchase.requisition'].browse(active_id)
        if not self.rejection_reason:
            raise UserError(_("Please provide a reason for rejection."))

        mr.rejection_reason = self.rejection_reason
        mr.action_reject_approval()
