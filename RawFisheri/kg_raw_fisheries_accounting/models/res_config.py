from ast import literal_eval
from odoo import models, fields


class KGResConfigInherit(models.TransientModel):
    _inherit = "res.config.settings"

    invoice_approvers_ids = fields.Many2many("res.users", string="Invoice Approvers")
    bill_approvers_ids = fields.Many2many("res.users", 'bill_aprv_ids', string="Bill Approvers")

    invoice_final_approvers_ids = fields.Many2many("res.users", 'invoice_final_aprv_ids')
    bill_final_approvers_ids = fields.Many2many("res.users", 'bill_final_aprv_ids')

    invoice_limit = fields.Monetary(string="Invoice Limit", currency_field="company_currency_id")
    bill_limit = fields.Monetary(string="Bill Limit", currency_field="company_currency_id")

    def set_values(self):
        res = super(KGResConfigInherit, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('kg_raw_fisheries_accounting.invoice_approvers_ids',
                                                         self.invoice_approvers_ids.ids)
        self.env['ir.config_parameter'].sudo().set_param('kg_raw_fisheries_accounting.bill_approvers_ids',
                                                         self.bill_approvers_ids.ids)

        self.env['ir.config_parameter'].sudo().set_param('kg_raw_fisheries_accounting.invoice_final_approvers_ids',
                                                         self.invoice_final_approvers_ids.ids)
        self.env['ir.config_parameter'].sudo().set_param('kg_raw_fisheries_accounting.bill_final_approvers_ids',
                                                         self.bill_final_approvers_ids.ids)

        self.env['ir.config_parameter'].sudo().set_param('kg_raw_fisheries_accounting.invoice_limit',
                                                         self.invoice_limit)
        self.env['ir.config_parameter'].sudo().set_param('kg_raw_fisheries_accounting.bill_limit',
                                                         self.bill_limit)
        return res

    def get_values(self):
        res = super(KGResConfigInherit, self).get_values()
        inv_approvers = self.env['ir.config_parameter'].sudo().get_param('kg_raw_fisheries_accounting.invoice_approvers_ids')
        bill_approvers = self.env['ir.config_parameter'].sudo().get_param('kg_raw_fisheries_accounting.bill_approvers_ids')

        inv_final_approvers = self.env['ir.config_parameter'].sudo().get_param('kg_raw_fisheries_accounting.invoice_final_approvers_ids')
        bill_final_approvers = self.env['ir.config_parameter'].sudo().get_param('kg_raw_fisheries_accounting.bill_final_approvers_ids')

        invoice_limit = self.env['ir.config_parameter'].sudo().get_param('kg_raw_fisheries_accounting.invoice_limit')
        bill_limit = self.env['ir.config_parameter'].sudo().get_param('kg_raw_fisheries_accounting.bill_limit')

        res.update(invoice_approvers_ids=[(6, 0, literal_eval(inv_approvers))] if inv_approvers else [],
                   bill_approvers_ids=[(6, 0, literal_eval(bill_approvers))] if bill_approvers else [],
                   invoice_final_approvers_ids=[(6, 0, literal_eval(inv_final_approvers))] if inv_final_approvers else [],
                   bill_final_approvers_ids=[(6, 0, literal_eval(bill_final_approvers))] if bill_final_approvers else [],
                   invoice_limit = invoice_limit,
                   bill_limit = bill_limit,
                   )
        return res
