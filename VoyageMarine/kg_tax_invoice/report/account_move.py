from ast import literal_eval

from odoo import models, fields,api

class AccountMove(models.Model):
    _inherit = 'account.move'


    # @api.model
    # def _get_report_values(self, docids, data=None):
    #     purchase_manager_ids = self.env['ir.config_parameter'].sudo().get_param('kg_tax_invoice.purchase_manager_ids')
    #     purchase_manager_info = []
    #
    #     if purchase_manager_ids:
    #         purchase_manager_ids = literal_eval(purchase_manager_ids)
    #         purchase_managers = self.env['res.users'].browse(purchase_manager_ids)
    #         purchase_manager_info = purchase_managers.mapped(lambda pm: {
    #             'name': pm.name,
    #             'phone': pm.partner_id.phone
    #         })
    #
    #     general_manager_ids = self.env['ir.config_parameter'].sudo().get_param('kg_tax_invoice.general_manager_ids')
    #     general_manager_info = []
    #
    #     if general_manager_ids:
    #         general_manager_ids = literal_eval(general_manager_ids)
    #         general_managers = self.env['res.users'].browse(general_manager_ids)
    #         general_manager_info = general_managers.mapped(lambda gm: {
    #             'name': gm.name,
    #             'phone': gm.partner_id.phone
    #         })
    #
    #     return {
    #         'doc_ids': docids,
    #         'doc_model': 'purchase.order',
    #         'docs': self.env['purchase.order'].browse(docids),
    #         'purchase_manager_info': purchase_manager_info,
    #         'general_manager_info': general_manager_info,
    #     }