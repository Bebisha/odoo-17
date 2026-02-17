from ast import literal_eval
from odoo import fields, models


class SalesResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    quotation_approve_ids = fields.Many2many('res.users', 'quotation_approve_ids_rel', string='Quotation Approval')
    hod_approve_ids = fields.Many2many('res.users', 'hod_approve_ids_rel', string='Head of Department')
    supervisor_ids = fields.Many2many('res.users', 'supervisor_approve_ids_rel', string='Supervisor')
    customer_ids = fields.Many2many('res.users', 'customer_approval_ids_rel', string='Customer')
    sale_revision_users_ids = fields.Many2many('res.users', 'sale_revision_approval_ids_rel', string='Revision Approval Users')
    hr_expense_alias_domain_id =fields.Char()
    def set_values(self):
        res = super(SalesResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('quotation_approve_ids',self.quotation_approve_ids.ids)
        self.env['ir.config_parameter'].sudo().set_param('hod_approve_ids',self.hod_approve_ids.ids)
        self.env['ir.config_parameter'].sudo().set_param('supervisor_ids',self.supervisor_ids.ids)
        self.env['ir.config_parameter'].sudo().set_param('kg_voyage_marine_sale.sale_revision_users_ids',self.sale_revision_users_ids.ids)
        self.env['ir.config_parameter'].sudo().set_param('kg_voyage_marine_sale.customer_ids',
                                                         self.customer_ids.ids)
        return res

    def get_values(self):
        sup = super(SalesResConfigSettings, self).get_values()
        qtn_approve_users = self.env['ir.config_parameter'].sudo().get_param('quotation_approve_ids')
        hod_approve_users = self.env['ir.config_parameter'].sudo().get_param('hod_approve_ids')
        supervisor_users = self.env['ir.config_parameter'].sudo().get_param('supervisor_ids')
        customer_user = self.env['ir.config_parameter'].sudo().get_param('kg_voyage_marine_sale.customer_ids')
        sale_revision_user = self.env['ir.config_parameter'].sudo().get_param('kg_voyage_marine_sale.sale_revision_users_ids')
        sup.update(quotation_approve_ids=[(6, 0, literal_eval(qtn_approve_users))] if qtn_approve_users else [],
                   hod_approve_ids=[(6, 0, literal_eval(hod_approve_users))] if hod_approve_users else [],
                   supervisor_ids=[(6, 0, literal_eval(supervisor_users))] if supervisor_users else [],
                   customer_ids=[(6, 0, literal_eval(customer_user))] if customer_user else [],
                   sale_revision_users_ids=[(6, 0, literal_eval(sale_revision_user))] if sale_revision_user else [],
                   )
        return sup