from odoo import models, fields, api

from odoo.addons.web_approval.models.approval_mixin import _APPROVAL_STATES


class PurchaseOrderInh(models.Model):
    _name = "purchase.order"
    _inherit = ['purchase.order', 'mail.activity.mixin', 'approval.mixin', 'mail.thread']

    contract_number = fields.Char(string='Contract number')
    approvals = fields.Json('Approval Flow')
    approval_state = fields.Selection(string='Approval Status', selection=_APPROVAL_STATES, required=False, copy=False,
                                      is_approval_state=True, tracking=True)
