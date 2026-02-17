from odoo import models, fields
from odoo.exceptions import ValidationError


class TDRejectReasonWizard(models.TransientModel):
    _name = "td.reject.reason.wizard"
    _description = "TD Reject Reason Wizard"

    name = fields.Char(string="Name")
    td_id = fields.Many2one("transaction.documents", string="TD")
    td_line_id = fields.Many2one("transaction.documents.line", string="TD Line")
    reason = fields.Char(string="Reason")

    def action_submit_reject(self):
        if not self.reason:
            raise ValidationError("Please provide a reason before rejecting")
