from ast import literal_eval

from odoo import models, fields, api


class PurchaseOrderConfiguring(models.TransientModel):
    _inherit = 'res.config.settings'

    purchase_manager_ids = fields.Many2many('res.users', 'po_finance_rel', string='Purchase Manager')
    vendor_approval_ids = fields.Many2many('res.users', 'po_vendor_approval_rel', string='Vendor Approval')
    general_manager_ids = fields.Many2many('res.users', 'po_operations_rel', string='GM')
    finance_manager_ids = fields.Many2many('res.users', 'po_finance_manager_rel', string='Finance Manager')
    line_manager_ids = fields.Many2many('res.users', 'line_manager_rel', string='Line Manager')
    department_manager_ids = fields.Many2many('res.users', 'department_manager_rel', string='Department Manager')
    hr_manager_ids = fields.Many2many('res.users', 'hr_manager_rel', string='HR Manager')
    account_team_ids = fields.Many2many('res.users', 'nt_team_rel', string='Account Teams')
    account_credit_limit_action = fields.Selection([
        ('warning', 'Warning'),
        ('blocking', 'Blocking')
    ], string="Credit Limit Action", default='warning', help="Choose whether to show a warning or block the sale.")

    def set_values(self):
        res = super(PurchaseOrderConfiguring, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('kg_purchase.purchase_manager_ids',
                                                         self.purchase_manager_ids.ids)
        self.env['ir.config_parameter'].sudo().set_param('kg_purchase.vendor_approval_ids',
                                                         self.vendor_approval_ids.ids)
        self.env['ir.config_parameter'].sudo().set_param('kg_purchase.general_manager_ids',
                                                         self.general_manager_ids.ids)
        self.env['ir.config_parameter'].sudo().set_param('kg_purchase.finance_manager_ids',
                                                         self.finance_manager_ids.ids)
        self.env['ir.config_parameter'].sudo().set_param('kg_purchase.line_manager_ids',
                                                         self.line_manager_ids.ids)
        self.env['ir.config_parameter'].sudo().set_param('kg_purchase.department_manager_ids',
                                                         self.department_manager_ids.ids)
        self.env['ir.config_parameter'].sudo().set_param('kg_purchase.hr_manager_ids',
                                                         self.hr_manager_ids.ids)
        self.env['ir.config_parameter'].sudo().set_param('kg_purchase.account_team_ids',
                                                         self.account_team_ids.ids)
        self.env['ir.config_parameter'].sudo().set_param('kg_purchase.account_credit_limit_action',
                                                         self.account_credit_limit_action)

        return res

    def get_values(self):
        sup = super(PurchaseOrderConfiguring, self).get_values()
        with_user = self.env['ir.config_parameter'].sudo()
        purchase_manager = with_user.get_param('kg_purchase.purchase_manager_ids')
        vendor_approval = with_user.get_param('kg_purchase.vendor_approval_ids')
        general_manager = with_user.get_param('kg_purchase.general_manager_ids')
        finance_manager = with_user.get_param('kg_purchase.finance_manager_ids')
        line_manager = with_user.get_param('kg_purchase.line_manager_ids')
        department_manager = with_user.get_param('kg_purchase.department_manager_ids')
        hr_manager = with_user.get_param('kg_purchase.hr_manager_ids')
        account_team = with_user.get_param('kg_purchase.account_team_ids')
        account_credit_limit_action = with_user.get_param('kg_purchase.account_credit_limit_action')


        sup.update(purchase_manager_ids=[(6, 0, literal_eval(purchase_manager))] if purchase_manager else [],
                   vendor_approval_ids=[(6, 0, literal_eval(vendor_approval))] if vendor_approval else [],
                   general_manager_ids=[(6, 0, literal_eval(general_manager))] if general_manager else [],
                   finance_manager_ids=[(6, 0, literal_eval(finance_manager))] if finance_manager else [],
                   line_manager_ids=[(6, 0, literal_eval(line_manager))] if line_manager else [],
                   department_manager_ids=[(6, 0, literal_eval(department_manager))] if department_manager else [],
                   hr_manager_ids=[(6, 0, literal_eval(hr_manager))] if hr_manager else [],
                   account_team_ids=[(6, 0, literal_eval(account_team))] if account_team else [],
                   account_credit_limit_action = account_credit_limit_action if account_credit_limit_action else []
                   )
        return sup
